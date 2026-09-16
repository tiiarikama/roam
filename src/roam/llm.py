from openai import OpenAI
from roam.settings import settings

sync_client = OpenAI(api_key=settings.openai_api_key.get_secret_value())

