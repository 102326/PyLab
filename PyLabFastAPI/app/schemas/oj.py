# app/schemas/oj.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProblemOut(BaseModel):
    id: int
    title: str
    content: str
    init_code: str
    time_limit: int
    memory_limit: int

    class Config:
        from_attributes = True


class SubmitReq(BaseModel):
    problem_id: int
    code: str
    language: str = "python"


class SubmissionOut(BaseModel):
    id: str
    status: str  # PENDING, AC, WA, TLE, RE
    error_msg: Optional[str] = None
    time_cost: Optional[int] = None
    memory_cost: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ProblemCreateReq(BaseModel):
    title: str
    content: str
    init_code: str = ""
    time_limit: int = 1000
    memory_limit: int = 128