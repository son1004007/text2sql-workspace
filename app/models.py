from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AttemptStatus(StrEnum):
    RECEIVED = "RECEIVED"
    GENERATED = "GENERATED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VALIDATED = "VALIDATED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EXECUTED = "EXECUTED"
    GENERATION_FAILED = "GENERATION_FAILED"
    SUCCEEDED = "SUCCEEDED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)

    workspaces: Mapped[list["Workspace"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    owner: Mapped[User] = relationship(back_populates="workspaces")
    queries: Mapped[list["QueryRecord"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class QueryRecord(Base):
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id"), index=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    workspace: Mapped[Workspace] = relationship(back_populates="queries")
    attempts: Mapped[list["QueryAttempt"]] = relationship(
        back_populates="query",
        cascade="all, delete-orphan",
        order_by="QueryAttempt.attempt_number",
    )


class QueryAttempt(Base):
    __tablename__ = "query_attempts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    query_id: Mapped[str] = mapped_column(ForeignKey("queries.id"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_of_attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("query_attempts.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=AttemptStatus.RECEIVED.value, nullable=False
    )
    candidate_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    query: Mapped[QueryRecord] = relationship(back_populates="attempts")
