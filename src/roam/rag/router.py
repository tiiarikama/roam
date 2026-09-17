import json
import asyncio

from roam.config import LLM_MODEL, TARGET_PARKS, PARK_METADATA, INTENT_CATEGORIES, MAX_ROUTER_TOKENS
from roam.llm import async_client


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
- off_topic: Not related to US national parks at all (e.g. "What's the weather in Paris?", "Give me a lasagna recipe!")

RULES:
- If a query mentions a specific park by name, it is park_specific — not general_parks
- For park_specific, return the relevant park code(s)
- For comparative with specific parks mentioned, return those park codes
- For comparative without specific parks, general_parks, and off_topic, return an empty parks array
- Set needs_weather to True if the query asks about current weather, current conditions, temperature, or what to wear/pack based on current weather. Set to False for general seasonal questions or any other non-weather related queries.

EXAMPLES:
"What permits do I need for Half Dome?"
intent: park_specific
parks: yose
needs_weather: False

"Compare Zion and Yosemite for hiking"
intent: comparative
parks: zion,yose
needs_weather: False

"Which park is best for wildlife?"
intent: comparative
parks: none
needs_weather: False

"What should I bring on a hike right now based on weather?"
intent: general_parks
parks: none
needs_weather: True

"What should I bring on a hike?"
intent: general_parks
parks: none
needs_weather: False

"Thanks, that's really helpful!"
intent: greeting
parks: none
needs_weather: False

"What's the best restaurant in NYC?"
intent: off_topic
parks: none
needs_weather: False

"What's the weather like in Yosemite right now?"
intent: park_specific
parks: yose
needs_weather: True

"What's the best season to visit Zion?"
intent: park_specific
parks: zion
needs_weather: False

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
                "needs_weather": {
                    "type": "boolean",
                },
            },
            "required": ["intent", "parks", "needs_weather"],
            "additionalProperties": False,
        },
    },
}

FALLBACK_ROUTE = {
    "intent": "general_parks",
    "parks": [],
    "needs_weather": False
}

def build_router_prompt(last_park_codes=None) -> str:
    parks_list = "\n".join(f"- {code}: {data["name"]}" for code, data in PARK_METADATA.items())
    prompt = ROUTER_PROMPT.format(parks=parks_list)

    if last_park_codes:
        park_names = ", ".join(PARK_METADATA[code]["name"] for code in last_park_codes if code in PARK_METADATA)
        prompt += (
            f"\n\nCONVERSATION CONTEXT:\n"
            f"The user has been asking about: {park_names}.\n"
            f"If the query is an ambiguous follow-up that could plausibly relate to these parks "
            f"(e.g. 'what about food there?', 'how's the camping?'), classify it as park_specific "
            f"and return the relevant park code(s). Only classify as off_topic if the query is "
            f"clearly unrelated to national parks (e.g. 'give me a lasagna recipe')."
        )

    return prompt

def parse_route(content: str) -> dict:
    result = json.loads(content)

    result["parks"] = [code for code in result.get("parks", []) if code in TARGET_PARKS]
    result.setdefault("needs_weather", False)

    if result.get("intent") not in INTENT_CATEGORIES:
        result["intent"] = "general_parks"

    return result


# classifies query intent and detects relevant park(s)
async def route_query(query: str, last_park_codes: list[str] = None) -> dict:
    prompt = build_router_prompt(last_park_codes)

    try:
        response = await async_client.chat.completions.create(
            model=LLM_MODEL,
            max_tokens=MAX_ROUTER_TOKENS,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": query,
                },
            ],
            response_format=ROUTER_RESPONSE_FORMAT,
        )

        return parse_route(response.choices[0].message.content)
    except (json.JSONDecodeError, TypeError, KeyError) as error:
        print(f"Router returned an unusable payload: {error}")
        return dict(FALLBACK_ROUTE)
    except Exception as error:
        print(f"Router call failed: {error}")
        return dict(FALLBACK_ROUTE)

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

    async def main():
        for query in test_queries:
            result = await route_query(query)
            print(f"Q: {query}")
            print(f"   → intent: {result['intent']}, parks: {result['parks']}, weather: {result['needs_weather']}")
            print()

    asyncio.run(main())