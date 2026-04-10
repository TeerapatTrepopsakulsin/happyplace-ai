from pydantic import BaseModel
from typing import List


class GuidelinesResponse(BaseModel):
    id: str
    patient_id: str
    authored_by: str
    response_tone: str | None
    coping_strategies: str | None
    behavioral_boundaries: str | None
    sensitive_topics: List[str] | None
    updated_at: str  # datetime as string


class GuidelinesUpdateRequest(BaseModel):
    response_tone: str | None = None
    coping_strategies: str | None = None
    behavioral_boundaries: str | None = None
    sensitive_topics: List[str] | None = None
