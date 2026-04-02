import json
from openai import OpenAI
from roam.config import OPENAI_API_KEY, LLM_MODEL, TARGET_PARKS, PARK_METADATA, INTENT_CATEGORIES

client = OpenAI(api_key=OPENAI_API_KEY)

ROUTER_PROMPT = """
You are a query router for a national parks trip planning assistant. Given a user question, 
classify the intent and identify which park(s) it relates to.

AVAILABLE PARKS:
{parks}

INTENT CATEGORIES:
- park_specific: Question about one or more specific parks (e.g. "What permits do I need for Half Dome?", "Is Yellowstone open in winter?")
- comparative: Comparing parks or asking which park is best for something (e.g. "Does Yosemite or Grand Canyon have better hiking?", "Which park has the best hiking?")
- general_parks: General national park question not about a specific park (e.g. "What should I pack for a national park trip?")
- greeting: Greetings, thanks, casual conversation, or brief reactions to a previous answer (e.g. "Hey!", "Thanks that's helpful", "Great!", "Hello, can you help me?")
- off_topic: Not related to US national parks at all (e.g. "What's the weather in Paris?")

RULES:
- If a query mentions a specific park by name, it is park_specific — not general_parks
- For park_specific, return the relevant park code(s)
- For comparative with specific parks mentioned, return those park codes
- For comparative without specific parks, general_parks, and off_topic, return an empty parks array

EXAMPLES:
"What permits do I need for Half Dome?"
intent: park_specific
parks: yose

"Compare Zion and Yosemite for hiking"
intent: comparative
parks: zion,yose

"Which park is best for wildlife?"
intent: comparative
parks: none

"What should I bring on a hike?"
intent: general_parks
parks: none

"Thanks, that's really helpful!"
intent: greeting
parks: none

"What's the best restaurant in NYC?"
intent: off_topic
parks: none
"""

ROUTER_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "route_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": list(INTENT_CATEGORIES),
                },
                "parks": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["intent", "parks"],
            "additionalProperties": False,
        },
    },
}


# classifies query intent and detects relevant park(s)
def route_query(query: str) -> dict:
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
            response_format=ROUTER_RESPONSE_FORMAT,
        )
    except Exception as e:
        print(f"Router error occurred: {e}")
        return {"intent": "general_parks", "parks": []}
    
    result = json.loads(response.choices[0].message.content)
    result["parks"] = [code for code in result["parks"] if code in TARGET_PARKS]

    return result

if __name__ == "__main__":
    test_queries = [
        "How do I get a Half Dome permit?",
        "What are beginner friendly hikes in Yosemite?",
        "What are the best trails at the Grand Canyon?",
        "Compare Zion and Yosemite for hiking",
        "Which park is best for wildlife watching?",
        "What should I pack for a national park trip?",
        "Is Yellowstone open in winter?",
        "What's the best pizza in New York?",
    ]

    for query in test_queries:
        result = route_query(query)
        print(f"Q: {query}")
        print(f"   → intent: {result['intent']}, parks: {result['parks']}")
        print()