from openai import OpenAI, AsyncOpenAI
from roam.settings import settings

sync_client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
async_client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
