import os

from langchain_groq import ChatGroq
from pydantic import SecretStr


def get_llm_client() -> ChatGroq:
    model_name = os.getenv("GROQ_MODEL")
    api_key = os.getenv("GROQ_API_KEY")
    if not model_name or not api_key:
        raise ValueError("GROQ_MODEL or GROQ_API_KEY is not set")
    return ChatGroq(model=model_name, api_key=SecretStr(api_key))
