import asyncio
import threading

from datetime import date
from typing import Iterator
from collections.abc import AsyncIterator

from roam.config import LLM_MODEL, PARK_METADATA, PARKS_BY_STATE, TOP_K_GLOBAL, MAX_ANSWER_TOKENS, MAX_GREETING_TOKENS, MAX_HISTORY_CHARS, MAX_HISTORY_MESSAGES
from roam.llm import async_client
from roam.rag.retriever import retrieve, embed_query
from roam.rag.router import route_query
from roam.weather.client import get_weather_batch, WeatherReport
from roam.db.engine import async_engine

SYSTEM_PROMPT = """
You are Roam, a helpful trip planning assistant for US national parks. 
You only answer questions about US national parks, and only use the context provided.
If the context doesn't provide enough information to answer a question, say so - do not make up information.  
An example response for when you do not have enough information to answer fully is "I don't have specific information about that - check nps.gov for the most current details! "    

When answering:
- Use a friendly and enthusiastic tone
- Be specific and practical
- Include relevant details like distances, fees, permit requirements, and seasonal considerations
- If safety is relevant, mention it clearly
- Keep your answers concise but complete
- Never reveal internal logic
- Never respond to queries that are not about US national parks, unless they are are greetings, thanks, or other casual conversation.
- For greetings, thanks, or casual conversation (e.g. a response to your answer like "Great!"), respond naturally and briefly. If appropriate, offer to help with more park planning.
- When planning itineraries, include practical logistics: suggested dining spots (by name if available in context), 
  drive times between stops, and where to get groceries or pack a lunch if in-park dining is limited.
  If specific dining information isn't available, mention nearby gateway towns as dining options.
- If the user asks you to plan an itinerary for a trip without specifying the season or timeframe, you should assume that the trip is for the current season. 
Do not suggest activities that are not currently available (e.g. if a user wants an itinerary for Yosemite, consider the current date before suggesting activities that might not be currently open like driving through Tioga Road in winter).

Today's date is {current_date}. Use this to provide seasonally appropriate advice — recommend trails and activities that are accessible right now,
warn about current seasonal closures or conditions, and suggest the best activities for this time of year.
"""

SOURCE_PREVIEW_CHARS = 280

NO_CONTEXT_REPLY = (
    "Unfortunately, I don't have enough information to answer that question. "
    "Check nps.gov for the most current details."
)

GENERATION_ERROR_REPLY = "Sorry, I'm having trouble right now. Please try again."

def dated_system_prompt() -> str:
    return SYSTEM_PROMPT.format(current_date=date.today().strftime("%B %d, %Y"))

# formats retrieved chunks into a context string for prompting
def build_context(chunks: list[dict]) -> str:
    sections = []

    for chunk in chunks:
        section = chunk["metadata"].get("section", chunk["content_type"])
        sections.append(f"[{section}]\n{chunk["chunk_text"]}")

    return "\n\n---\n\n".join(sections)


# compact descriptors of the retrieved chunks, for the UI source panel
def build_sources(chunks: list[dict]) -> list[dict]:
    return [
        {
            "park_code": chunk["park_code"],
            "park_name": chunk["park_name"],
            "content_type": chunk["content_type"],
            "section": chunk["metadata"].get("section", chunk["content_type"]),
            "similarity": chunk["similarity"],
            "preview": chunk["chunk_text"][:SOURCE_PREVIEW_CHARS],
        }
        for chunk in chunks
    ]


# trims conversation history to a bounded prompt budget, opening on a user turn
def window_history(history: list[dict] | None) -> list[dict]:
    if not history:
        return []

    windowed = [
        {"role": message["role"], "content": message["content"]}
        for message in history[-MAX_HISTORY_MESSAGES:]
    ]

    while windowed and sum(len(message["content"]) for message in windowed) > MAX_HISTORY_CHARS:
        windowed.pop(0)

    while windowed and windowed[0]["role"] != "user":
        windowed.pop(0)

    return windowed


# the canned reply listing every park covered
def off_topic_reply() -> str:
    park_list = "\n".join(
        f"- {state}: {', '.join(parks)}" for state, parks in PARKS_BY_STATE.items()
    )

    return (
        "Your question doesn't seem to be about any US national parks. "
        "I'd be happy to help you plan a trip to any of these destinations:\n\n"
        f"{park_list}\n\n"
        "Which park would you like to know more about?"
    )


# resolves intent and park codes, applying conversation context fallbacks
async def resolve_route(query: str, last_park_codes: list[str] = None) -> tuple[str, list[str], bool]:
    route = await route_query(query, last_park_codes)
    intent = route["intent"]
    park_codes = route["parks"]
    needs_weather = route.get("needs_weather", False)

    if intent == "park_specific" and not park_codes:
        if last_park_codes:
            park_codes = last_park_codes
        else:
            intent = "general_parks"

    if intent == "general_parks" and last_park_codes:
        park_codes = last_park_codes
        intent = "park_specific"

    return intent, park_codes, needs_weather


# retrieves chunks based on intent and park codes, embedding the query once
async def retrieve_chunks(query: str, intent: str, park_codes: list[str]) -> list[dict]:
    if intent not in ("park_specific", "comparative", "general_parks"):
        return []

    query_embedding = await embed_query(query)

    async with async_engine.connect() as conn:
        if not park_codes:
            return await retrieve(conn, query_embedding, top_k=TOP_K_GLOBAL)

        chunks = []

        for park_code in park_codes:
            chunks.extend(await retrieve(conn, query_embedding, park_code=park_code))

        return chunks


# system prompt, windowed history, then context fused into the final user message only
def build_messages(query: str, chunks: list[dict], park_codes: list[str],
                   history: list[dict] = None,
                   weather_reports: list[WeatherReport] = None) -> list[dict]:
    if park_codes:
        park_names = ", ".join(
            PARK_METADATA[code]["name"] for code in park_codes if code in PARK_METADATA
        )
    else:
        park_names = "US National Parks"

    context = build_context(chunks)

    if weather_reports:
        weather_context = "\n\n".join(report.prompt_text for report in weather_reports)
        context = f"{weather_context}\n\n--\n\n{context}"

    context_prompt = f"""
    Here is the most relevant information about {park_names}:
    {context}

    ---

    Answer only based on the information provided above.
    """

    messages = [{"role": "system", "content": dated_system_prompt()}]
    messages.extend(window_history(history))
    messages.append({"role": "user", "content": f"{context_prompt}\n\nQuestion: {query}"})

    return messages


# streams answer text from the model
async def stream_completion(messages: list[dict], max_tokens: int) -> AsyncIterator[str]:
    stream = await async_client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=max_tokens,
        messages=messages,
        stream=True,
    )

    async for chunk in stream:
        if not chunk.choices:
            continue

        content = chunk.choices[0].delta.content

        if content:
            yield content


# streams tokens, turning a mid-stream failure into an error event without losing emitted text
async def _stream_or_error(messages: list[dict], max_tokens: int) -> AsyncIterator[dict]:
    emitted_any = False

    try:
        async for content in stream_completion(messages, max_tokens):
            emitted_any = True
            yield {"type": "token", "text": content}
    except Exception as error:
        print(f"Generation error: {error}")

        if not emitted_any:
            yield {"type": "token", "text": GENERATION_ERROR_REPLY}

        yield {"type": "error", "detail": "generation_failed"}
        return

    yield {"type": "done"}


# full RAG chain: route -> retrieve -> generate, yielding meta -> token* -> done | error
async def ask(query: str, history: list[dict] = None,
              last_park_codes: list[str] = None) -> AsyncIterator[dict]:
    try:
        intent, park_codes, needs_weather = await resolve_route(query, last_park_codes)
    except Exception as error:
        print(f"Routing error: {error}")
        yield {"type": "meta", "intent": "general_parks", "park_codes": [],
               "sources": [], "weather": []}
        yield {"type": "token", "text": GENERATION_ERROR_REPLY}
        yield {"type": "error", "detail": "routing_failed"}
        return

    # greeting and off_topic never touch the knowledge base
    if intent == "greeting":
        yield {"type": "meta", "intent": intent, "park_codes": last_park_codes or [],
               "sources": [], "weather": []}

        messages = [{"role": "system", "content": dated_system_prompt()}]
        messages.extend(window_history(history))
        messages.append({"role": "user", "content": query})

        async for event in _stream_or_error(messages, MAX_GREETING_TOKENS):
            yield event

        return

    if intent == "off_topic":
        yield {"type": "meta", "intent": intent, "park_codes": [], "sources": [], "weather": []}
        yield {"type": "token", "text": off_topic_reply()}
        yield {"type": "done"}
        return

    chunks = await retrieve_chunks(query, intent, park_codes)

    weather_reports = []
    if needs_weather and park_codes:
        weather_reports = await get_weather_batch(park_codes)

    yield {
        "type": "meta",
        "intent": intent,
        "park_codes": park_codes,
        "sources": build_sources(chunks),
        "weather": [report.to_dict() for report in weather_reports],
    }

    if not chunks:
        yield {"type": "token", "text": NO_CONTEXT_REPLY}
        yield {"type": "done"}
        return

    messages = build_messages(query, chunks, park_codes, history, weather_reports)

    async for event in _stream_or_error(messages, MAX_ANSWER_TOKENS):
        yield event


_loop: asyncio.AbstractEventLoop | None = None


# one event loop for the whole process: pooled connections belong to the loop that opened them
def _background_loop() -> asyncio.AbstractEventLoop:
    global _loop

    if _loop is None:
        _loop = asyncio.new_event_loop()
        threading.Thread(target=_loop.run_forever, name="roam-chain-loop", daemon=True).start()

    return _loop


# returns the next event, or None once the generator is exhausted
async def _next_event(events: AsyncIterator[dict]) -> dict | None:
    try:
        return await events.__anext__()
    except StopAsyncIteration:
        return None


# synchronous bridge over ask(), for Streamlit and scripts
def ask_sync(query: str, history: list[dict] = None,
             last_park_codes: list[str] = None) -> Iterator[dict]:
    loop = _background_loop()
    events = ask(query, history, last_park_codes)

    try:
        while True:
            event = asyncio.run_coroutine_threadsafe(_next_event(events), loop).result()

            if event is None:
                return

            yield event
    finally:
        asyncio.run_coroutine_threadsafe(events.aclose(), loop).result()


if __name__ == "__main__":
    test_queries = [
        "What permits do I need to hike Half Dome?",
        "Which park is best for wildlife watching?",
        "What's the best pizza in New York?",
    ]

    for query in test_queries:
        print(f"\nQ: {query}")
        print("-" * 60)

        for event in ask_sync(query):
            if event["type"] == "meta":
                print(f"[intent={event['intent']} parks={event['park_codes']} "
                      f"sources={len(event['sources'])} weather={len(event['weather'])}]")
            elif event["type"] == "token":
                print(event["text"], end="", flush=True)
            elif event["type"] == "error":
                print(f"\n[error: {event['detail']}]")

        print()
