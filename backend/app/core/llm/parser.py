import json

VALID_EMOTION_LABELS = {"happy", "sad", "anxious", "angry", "neutral", "distressed"}


def parse_chat_response(raw_content) -> str:
    if raw_content is None:
        return ""
    return str(raw_content)


def parse_emotion_analysis_response(raw_response: str) -> dict:
    try:
        parsed = json.loads(raw_response)
        label = parsed.get("emotion_label", "neutral")
        score = parsed.get("emotion_score", 0.0)

        if not isinstance(label, str) or label.lower() not in VALID_EMOTION_LABELS:
            label = "neutral"

        try:
            score = float(score)
            if score < 0.0 or score > 1.0:
                score = 0.0
        except Exception:
            score = 0.0

        return {"emotion_label": label.lower(), "emotion_score": score}
    except Exception:
        return {"emotion_label": "neutral", "emotion_score": 0.0}
