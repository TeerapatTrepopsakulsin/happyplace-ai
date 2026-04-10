from sqlalchemy import select

from app.core.llm import (
    build_chat_system_prompt,
    build_history_messages,
    run_chat_chain,
)
from app.models.chatbot_guidelines import ChatbotGuidelines
from app.services.cache import get_session_messages, invalidate_session_messages


async def get_guidelines(user_id, db):
    stmt = select(ChatbotGuidelines).where(ChatbotGuidelines.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def build_system_prompt(guidelines):
    return build_chat_system_prompt(guidelines)


async def get_conversation_history(session_id, redis, db):
    messages = await get_session_messages(session_id, redis, db)
    return build_history_messages(messages)


async def call_groq(system_prompt, history, user_content):
    return await run_chat_chain(system_prompt, history, user_content)


async def update_session_cache(session_id, redis, db):
    await invalidate_session_messages(session_id, redis)
    # Refresh by calling get_session_messages
    await get_session_messages(session_id, redis, db)
