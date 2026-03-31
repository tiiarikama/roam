from openai import OpenAI
from roam.config import OPENAI_API_KEY, LLM_MODEL, TARGET_PARKS, PARK_METADATA

client = OpenAI(api_key=OPENAI_API_KEY)

ROUTER_PROMPT = """
You are a national park query router. Given a user question, your job is to identify which national park the 
user query is about.

AVAILABLE PARKS:
{parks}

RULES:
- If the question is clearly about one specific park, return only that park's code
- If the question mentions multiple parks, return all relevant codes comma-separated
- If the question is general and not about a specific park, return "none"
- Return only the park code(s) or "none" — no explanation

EXAMPLES:
"How do I get a Half Dome permit?" → yose
"What trails are at the Grand Canyon?" → grca
"Compare Zion and Yosemite for hiking" → zion,yose
"Which park is best for wildlife?" → none
"""

# detects which park(s) a user query is about
def detect_park(query: str) -> list[str]:
    parks_list = "\n".join(f"- {code}: {name}" for code, name in PARK_METADATA.items())

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=50,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": ROUTER_PROMPT.format(parks=parks_list),
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
        )
    except Exception as e:
        print(f"Router error occurred: {e}")
        return []
    
    result = response.choices[0].message.content.strip().lower()

    if result == "none" or not result:
        return []
    
    codes = [code.strip() for code in result.split(",")]
    valid_codes = []

    for code in codes:
        if code in TARGET_PARKS:
            valid_codes.append(code)

    return valid_codes

if __name__ == "__main__":
    test_queries = [
        "How do I get a Half Dome permit?",
        "What are beginner friendly hikes in Yosemite?",
        "What are the best trails at the Grand Canyon?",
        "Compare Zion and Yosemite for hiking",
        "Which park is best for wildlife watching?",
        "Is Yellowstone open in winter?",
        "What should I pack for a trip to Acadia?", 
    ]

    for query in test_queries:
        parks = detect_park(query)
        print(f"Q: {query}")
        print(f"   → {parks if parks else 'no park detected'}")
        print()