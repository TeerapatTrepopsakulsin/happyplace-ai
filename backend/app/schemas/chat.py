from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: str
    title: str | None
    created_at: str
    last_active: str | None


class MessageResponse(BaseModel):
    id: str
    sender: str
    content: str
    emotion_label: str | None
    emotion_score: float | None
    danger_flag: bool
    created_at: str


class SendMessageRequest(BaseModel):
    content: str


class SessionUpdateRequest(BaseModel):
    title: str


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
