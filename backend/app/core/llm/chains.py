from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.llm.client import get_llm_client
from app.core.llm.parser import parse_chat_response, parse_emotion_analysis_response
from app.core.llm.prompt import build_emotion_analysis_prompt


def build_chat_messages(
    system_prompt: str, history: list[HumanMessage | AIMessage], user_content: str
) -> list[SystemMessage | HumanMessage | AIMessage]:
    return (
        [SystemMessage(content=system_prompt)]
        + history
        + [HumanMessage(content=user_content)]
    )


def build_history_messages(messages: list[dict]) -> list[HumanMessage | AIMessage]:
    history: list[HumanMessage | AIMessage] = []
    for msg in messages[-10:]:
        if msg["sender"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["sender"] == "assistant":
            history.append(AIMessage(content=msg["content"]))
    return history


async def run_chat_chain(
    system_prompt: str, history: list[HumanMessage | AIMessage], user_content: str
) -> str:
    llm = get_llm_client()
    response = await llm.ainvoke(
        build_chat_messages(system_prompt, history, user_content)
    )
    return parse_chat_response(response.content)


async def run_emotion_chain(content: str) -> dict:
    llm = get_llm_client()
    prompt = build_emotion_analysis_prompt(content)
    response = await llm.ainvoke(
        [SystemMessage(content=prompt), HumanMessage(content=content)]
    )
    return parse_emotion_analysis_response(str(response.content))
