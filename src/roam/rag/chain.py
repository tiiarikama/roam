from openai import OpenAI
from datetime import date
from roam.config import OPENAI_API_KEY, LLM_MODEL, PARK_METADATA, PARKS_BY_STATE, TOP_K_GLOBAL
from roam.rag.retriever import retrieve
from roam.rag.router import route_query


client = OpenAI(api_key=OPENAI_API_KEY)

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

# formats retrieved chunks into a context string for prompting
def build_context(chunks: list[dict]) -> str:
    sections = []

    for chunk in chunks:
        section = chunk["metadata"].get("section", chunk["content_type"])
        sections.append(f"[{section}]\n{chunk["chunk_text"]}")
    
    return "\n\n---\n\n".join(sections)

# resolves intent and park codes, applying conversation context fallbacks
def resolve_route(query: str, last_park_codes: list[str] = None) -> tuple[str, list[str]]:
    route = route_query(query)
    intent = route["intent"]
    park_codes = route["parks"]

    if intent == "off_topic" and last_park_codes:
        park_codes = last_park_codes
        intent = "park_specific"
        
    if intent == "park_specific" and not park_codes:
        if last_park_codes:
            park_codes = last_park_codes
        else:
            intent = "general_parks"

    if intent == "general_parks" and last_park_codes:
        park_codes = last_park_codes
        intent = "park_specific"

    return intent, park_codes

# retrieves chunks based on intent and park codes
def retrieve_chunks(query: str, intent: str, park_codes: list[str]) -> list[dict]:
    if intent == "park_specific":
        chunks = []
        for code in park_codes:
            chunks.extend(retrieve(query, park_code=code))
        return chunks
    elif intent in ("comparative", "general_parks"):
        if park_codes:
            chunks = []

            for code in park_codes:
                chunks.extend(retrieve(query, park_code=code))
            return chunks
        else:
            return retrieve(query, top_k=TOP_K_GLOBAL)
    return []

def generate_response(query: str, chunks: list[dict], park_codes: list[str],
                      system_prompt: str, history: list[dict] = None) -> str:
    if park_codes:
        park_names = ", ".join(PARK_METADATA[code] for code in park_codes)
    else:
        park_names = "US National Parks"

    context = build_context(chunks)

    context_prompt = f"""
    Here is the most relevant information about {park_names}:
    {context}

    ---

    Answer only based on the information provided above.
    """

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": f"{context_prompt}\n\nQuestion: {query}"})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=1024,
        messages=messages,
    )

    return response.choices[0].message.content

def generate_greeting(query: str, system_prompt: str, history: list[dict] = None) -> str:
    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": query})

    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=256,
        messages=messages,
    )

    return response.choices[0].message.content

# full RAG chain: detect query intent and park codes -> retrieve relevant chunks -> generate answer
def ask(query: str, history: list[dict] = None, last_park_codes: list[str] = None) -> str:
    dated_system_prompt = SYSTEM_PROMPT.format(current_date=date.today().strftime("%B %d, %Y"))
    
    intent, park_codes = resolve_route(query, last_park_codes)

    if intent == "greeting":
        try:
            answer = generate_greeting(query, dated_system_prompt, history)
            return answer, last_park_codes or []
        except Exception as e:
            print(f"Chain error occurred: {e}")
            return "Sorry, I'm having trouble right now. Please try again.", last_park_codes or []


    if intent == "off_topic":
        park_list = "\n".join(
            f"- {state}: {', '.join(parks)}" for state, parks in PARKS_BY_STATE.items()
        )

        return (
            f"Your question doesn't seem to be about any US national parks. I'd be happy to help you plan a trip to any of these destinations:\n\n"
            f"{park_list}\n\n"
            "Which park would you like to know more about?",
            [],
        )
    
    all_chunks = retrieve_chunks(query, intent, park_codes)
    
    if not all_chunks:
        return (
            "Unfortunately, I don't have enough information to answer that question. "
            "Check nps.gov for the most current details.",
            park_codes,
        )

    try:
        answer = generate_response(query, all_chunks, park_codes, dated_system_prompt, history)
    except Exception as e:
        print(f"Chain error occurred: {e}")
        return "Sorry, I'm having trouble generating a response right now. Please try again.", park_codes
    
    return answer, park_codes

if __name__ == "__main__":
    test_queries = [
        "What permits do I need to hike Half Dome?",
        "Are there road closures at Yosemite right now?",
        "Where can I camp in Yosemite Valley and how do I book?",
        "Which park is best for wildlife watching?",
        "Compare Yosemite and Grand Canyon for hiking",
        "What's the best pizza in New York?",
    ]

    for query in test_queries:
        print(f"\nQ: {query}")
        print("-" * 60)
        answer, parks = ask(query)
        print(f"Parks: {parks}")
        print(answer)
        print()