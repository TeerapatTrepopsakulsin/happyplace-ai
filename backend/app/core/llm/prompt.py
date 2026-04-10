from app.models.chatbot_guidelines import ChatbotGuidelines

EMOTION_ANALYSIS_PROMPT_TEMPLATE = """
Analyze the emotional state expressed in the following text. Classify it with one of these emotion labels: happy, sad, anxious, angry, neutral, distressed.

Provide a score from 0.0 to 1.0 where:
- 1.0 = very happy/positive
- 0.5 = neutral
- 0.0 = very sad/distressed/negative

Respond only with valid JSON: {"emotion_label": "label", "emotion_score": 0.5}

Text: %s
"""


def build_chat_system_prompt(guidelines: ChatbotGuidelines | None) -> str:
    if guidelines is None:
        response_tone = "Not specified"
        coping_strategies = "Not specified"
        behavioral_boundaries = "Not specified"
        sensitive_topics = "Not specified"
        emotion_label = "unknown"
        emotion_score = "unknown"
    else:
        response_tone = str(guidelines.response_tone) or "Not specified"
        coping_strategies = str(guidelines.coping_strategies) or "Not specified"
        behavioral_boundaries = str(guidelines.behavioral_boundaries) or "Not specified"
        sensitive_topics = (
            ", ".join(str(topic) for topic in guidelines.sensitive_topics)
            if guidelines.sensitive_topics
            else "Not specified"
        )
        emotion_label = "unknown"
        emotion_score = "unknown"

    return f"""You are HappyPlaceAI, a compassionate mental health support chatbot.
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


def build_emotion_analysis_prompt(content: str) -> str:
    return EMOTION_ANALYSIS_PROMPT_TEMPLATE % content
