from pydantic import BaseModel
from typing import List, Optional

# ----- Auth Schemas -----
class TenantCreate(BaseModel):
    name: str
    display_name: str

class AuthRequest(BaseModel):
    username: str
    password: str
    tenant: str  # Tenant name identifier

# ----- Question Schemas -----
class QuestionCreate(BaseModel):
    question: str
    answer: bool

class QuestionResponse(BaseModel):
    id: int
    question: str
    # answer excluded intentionally (students shouldn't see answers)

# ----- Quiz Submission Schemas -----
class QuizSubmission(BaseModel):
    username: str
    answers: List[bool]

class QuizResult(BaseModel):
    message: str
    username: str
    score: int
    total: int