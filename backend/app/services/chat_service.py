import os
from sqlalchemy import select
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.models.chatbot_guidelines import ChatbotGuidelines
from app.services.cache import get_session_messages, invalidate_session_messages


async def get_guidelines(user_id, db):
    stmt = select(ChatbotGuidelines).where(ChatbotGuidelines.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def build_system_prompt(guidelines):
    if guidelines is None:
        response_tone = "Not specified"
        coping_strategies = "Not specified"
        behavioral_boundaries = "Not specified"
        sensitive_topics = "Not specified"
        emotion_label = "unknown"
        emotion_score = "unknown"
    else:
        response_tone = guidelines.response_tone or "Not specified"
        coping_strategies = guidelines.coping_strategies or "Not specified"
        behavioral_boundaries = guidelines.behavioral_boundaries or "Not specified"
        sensitive_topics = ", ".join(guidelines.sensitive_topics) if guidelines.sensitive_topics else "Not specified"
        emotion_label = "unknown"
        emotion_score = "unknown"

    prompt = f"""You are HappyPlaceAI, a compassionate mental health support chatbot.
Your role is to listen actively, validate emotions, and suggest coping strategies.
You are NOT a therapist or doctor. Do not provide clinical diagnoses.
Always follow safe-messaging guidelines for sensitive topics.

[THERAPIST GUIDELINES]
Tone: {response_tone}
Coping strategy focus: {coping_strategies}
Behavioral boundaries: {behavioral_boundaries}
Topics to avoid: {sensitive_topics}
[END GUIDELINES]

The user is currently feeling: {emotion_label} (confidence: {emotion_score}).
Adjust your empathy and language accordingly."""
    return prompt


async def get_conversation_history(session_id, redis, db):
    messages = await get_session_messages(session_id, redis, db)
    langchain_messages = []
    for msg in messages[-10:]:  # last 10 messages
        if msg['sender'] == 'user':
            langchain_messages.append(HumanMessage(content=msg['content']))
        elif msg['sender'] == 'assistant':
            langchain_messages.append(AIMessage(content=msg['content']))
    return langchain_messages


async def call_groq(system_prompt, history, user_content):
    model_name = os.getenv('GROQ_MODEL')
    api_key = os.getenv('GROQ_API_KEY')
    llm = ChatGroq(model=model_name, api_key=api_key)
    messages = [SystemMessage(content=system_prompt)] + history + [HumanMessage(content=user_content)]
    response = await llm.ainvoke(messages)
    return response.content


async def update_session_cache(session_id, redis, db):
    await invalidate_session_messages(session_id, redis)
    # Refresh by calling get_session_messages
    await get_session_messages(session_id, redis, db)