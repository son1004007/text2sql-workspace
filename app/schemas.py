from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DemoTokenRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    created_at: datetime


class QueryCreate(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class AttemptResponse(BaseModel):
    id: str
    attempt_number: int
    retry_of_attempt_id: str | None
    status: str
    candidate_sql: str | None
    failure_code: str | None
    result: dict[str, Any] | None
    created_at: datetime


class QueryResponse(BaseModel):
    id: str
    workspace_id: str
    question: str
    created_at: datetime
    attempts: list[AttemptResponse]


class EvaluationCaseResponse(BaseModel):
    case_id: str
    question: str
    generation_success: bool
    validation_success: bool
    execution_success: bool
    correctness_success: bool
    failure_code: str | None
    candidate_sql: str | None


class EvaluationSummaryResponse(BaseModel):
    total: int
    generation_success: int
    validation_success: int
    execution_success: int
    correctness_success: int
    cases: list[EvaluationCaseResponse]
