from openai import OpenAI
from roam.config import OPENAI_API_KEY, LLM_MODEL, PARK_METADATA, PARKS_BY_STATE
from roam.rag.retriever import retrieve
from roam.rag.router import detect_park

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are Roam, a helpful trip planning assistant for US national parks. 
You only answer questions about US national parks, and only use the context provided.
If the context doesn't provide enough information to answer a question, say so - do not make up information.  
An example response for when you do not have enough information to answer fully is "I don't have specific information about that - check nps.gov for the most current details. "    

When answering:
- Use a friendly and enthusiastic tone
- Be specific and practical
- Include relevant details like distances, fees, permit requirements, and seasonal considerations
- If safety is relevant, mention it clearly
- Keep your answers concise but complete
- Never reveal internal logic
- Never respond the queries that are not about US national parks"""

# formats retrieved chunks into a context string for prompting
def build_context(chunks: list[dict]) -> str:
    sections = []

    for chunk in chunks:
        section = chunk["metadata"].get("section", chunk["content_type"])
        sections.append(f"[{section}]\n{chunk["chunk_text"]}")
    
    return "\n\n---\n\n".join(sections)

# full RAG chain: detect_park -> retrieve relevant chunks -> generate answer
def ask(query: str, history: list[dict] = None, last_park_codes: list[str] = None) -> str:
    park_codes = detect_park(query)

    if not park_codes and last_park_codes:
        park_codes = last_park_codes

    if not park_codes:
        park_list = "\n".join(
            f"- {state}: {', '.join(parks)}" for state, parks in PARKS_BY_STATE.items()
        )

        return (
            f"Your question doesn't seem to be about any US national parks. I'd be happy to help you plan a trip to any of these destinations:\n\n"
            f"{park_list}\n\n"
            "Which park would you like to know more about?",
            [],
        )

    all_chunks = []

    for code in park_codes:
        all_chunks.extend(retrieve(query, park_code=code))

    if not all_chunks:
        return "Unfortunately I don't have enough information to answer that question. Please check nps.gov for the most current details."
    
    park_names = ", ".join(PARK_METADATA[code] for code in park_codes)
    context = build_context(all_chunks)

    context_prompt = f"""
    Here is the most relevant information about {park_names}:
    {context}

    ---

    Answer only based on the information provided above.
    """

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if history:
        messages.extend(history)

    messages.append({"role": "user", "content": f"{context_prompt}\n\nQuestion: {query}"})

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens = 1024,
            messages=messages,
        )
    except Exception as e:
        print(f"Chain error occurred: {e}")
        return "Sorry, I'm having trouble generating a response right now. Please try again."
    
    return response.choices[0].message.content, park_codes

if __name__ == "__main__":
    test_queries = [
        "What permits do I need to hike Half Dome?",
        "Are there road closures at Yosemite right now?",
        "Where can I camp in Yosemite Valley and how do I book?",
        "When is the best time to see waterfalls?",
        "Is there cell service in the park?",
        "Which park is best for wildlife watching?",
    ]

    for query in test_queries:
        print(f"\nQ: {query}")
        print("-" * 60)
        answer = ask(query)
        print(answer)
        print()