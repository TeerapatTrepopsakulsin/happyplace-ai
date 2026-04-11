from pydantic import BaseModel


class InvitationCreateRequest(BaseModel):
    invitee_email: str


class InvitationResponse(BaseModel):
    id: str
    invitee_email: str
    invitee_display_name: str | None
    role_granted: str
    created_at: str  # datetime as string


class InvitationListResponse(BaseModel):
    id: str
    invitee_email: str
    invitee_display_name: str | None
    role_granted: str
    created_at: str  # datetime as string
