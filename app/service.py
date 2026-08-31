from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics import QueryExecutionError, QueryExecutor
from app.auth import DEMO_USERS
from app.database import Database
from app.models import AttemptStatus, QueryAttempt, QueryRecord, User, Workspace
from app.schemas import AttemptResponse, QueryResponse, WorkspaceResponse
from app.sql_policy import SqlPolicyValidator, SqlPolicyViolation
from app.text2sql import Text2SqlGenerationError, Text2SqlModel


class ResourceNotFound(LookupError):
    pass


class Text2SqlWorkspaceService:
    def __init__(
        self,
        *,
        database: Database,
        model: Text2SqlModel,
        validator: SqlPolicyValidator,
        executor: QueryExecutor,
    ):
        self.database = database
        self.model = model
        self.validator = validator
        self.executor = executor

    def initialize(self) -> None:
        self.database.create_all()
        with self.database.session() as session:
            for user_id, display_name in DEMO_USERS.items():
                if session.get(User, user_id) is None:
                    session.add(User(id=user_id, display_name=display_name))

    def create_workspace(self, *, user_id: str, name: str) -> WorkspaceResponse:
        with self.database.session() as session:
            self._require_user(session, user_id)
            workspace = Workspace(owner_id=user_id, name=name.strip())
            session.add(workspace)
            session.flush()
            return self._workspace_response(workspace)

    def list_workspaces(self, *, user_id: str) -> list[WorkspaceResponse]:
        with self.database.session() as session:
            self._require_user(session, user_id)
            workspaces = session.scalars(
                select(Workspace)
                .where(Workspace.owner_id == user_id)
                .order_by(Workspace.created_at, Workspace.id)
            ).all()
            return [self._workspace_response(workspace) for workspace in workspaces]

    def get_workspace(self, *, user_id: str, workspace_id: str) -> WorkspaceResponse:
        with self.database.session() as session:
            workspace = self._owned_workspace(session, user_id, workspace_id)
            return self._workspace_response(workspace)

    def create_query(
        self,
        *,
        user_id: str,
        workspace_id: str,
        question: str,
    ) -> QueryResponse:
        with self.database.session() as session:
            workspace = self._owned_workspace(session, user_id, workspace_id)
            query = QueryRecord(workspace_id=workspace.id, question=question.strip())
            session.add(query)
            session.flush()

            attempt = QueryAttempt(query=query, attempt_number=1)
            session.add(attempt)
            session.flush()
            self._run_attempt(attempt, question=query.question)
            session.flush()
            return self._query_response(query)

    def retry_query(
        self,
        *,
        user_id: str,
        workspace_id: str,
        query_id: str,
    ) -> QueryResponse:
        with self.database.session() as session:
            query = self._owned_query(session, user_id, workspace_id, query_id)
            attempts = list(query.attempts)
            previous = attempts[-1] if attempts else None
            attempt = QueryAttempt(
                query=query,
                attempt_number=(previous.attempt_number + 1 if previous else 1),
                retry_of_attempt_id=(previous.id if previous else None),
            )
            session.add(attempt)
            session.flush()
            self._run_attempt(attempt, question=query.question)
            session.flush()
            return self._query_response(query)

    def list_queries(
        self,
        *,
        user_id: str,
        workspace_id: str,
    ) -> list[QueryResponse]:
        with self.database.session() as session:
            workspace = self._owned_workspace(session, user_id, workspace_id)
            queries = session.scalars(
                select(QueryRecord)
                .where(QueryRecord.workspace_id == workspace.id)
                .order_by(QueryRecord.created_at, QueryRecord.id)
            ).all()
            return [self._query_response(query) for query in queries]

    def get_query(
        self,
        *,
        user_id: str,
        workspace_id: str,
        query_id: str,
    ) -> QueryResponse:
        with self.database.session() as session:
            query = self._owned_query(session, user_id, workspace_id, query_id)
            return self._query_response(query)

    def _run_attempt(self, attempt: QueryAttempt, *, question: str) -> None:
        try:
            generated = self.model.generate(question=question)
        except Text2SqlGenerationError as exc:
            attempt.status = AttemptStatus.GENERATION_FAILED.value
            attempt.failure_code = str(exc)
            return

        attempt.candidate_sql = generated.sql
        attempt.status = AttemptStatus.GENERATED.value

        try:
            validation = self.validator.validate(generated.sql)
        except SqlPolicyViolation as exc:
            attempt.status = AttemptStatus.VALIDATION_FAILED.value
            attempt.failure_code = exc.code
            return

        attempt.status = AttemptStatus.VALIDATED.value
        try:
            result = self.executor.execute(validation.normalized_sql)
        except QueryExecutionError as exc:
            attempt.status = AttemptStatus.EXECUTION_FAILED.value
            attempt.failure_code = str(exc)
            return

        attempt.status = AttemptStatus.EXECUTED.value
        attempt.result_json = json.dumps(
            {
                "columns": list(result.columns),
                "rows": [list(row) for row in result.rows],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        attempt.status = AttemptStatus.SUCCEEDED.value

    @staticmethod
    def _require_user(session: Session, user_id: str) -> User:
        user = session.get(User, user_id)
        if user is None:
            raise ResourceNotFound("USER_NOT_FOUND")
        return user

    def _owned_workspace(
        self, session: Session, user_id: str, workspace_id: str
    ) -> Workspace:
        workspace = session.scalar(
            select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.owner_id == user_id,
            )
        )
        if workspace is None:
            raise ResourceNotFound("WORKSPACE_NOT_FOUND")
        return workspace

    def _owned_query(
        self,
        session: Session,
        user_id: str,
        workspace_id: str,
        query_id: str,
    ) -> QueryRecord:
        workspace = self._owned_workspace(session, user_id, workspace_id)
        query = session.scalar(
            select(QueryRecord).where(
                QueryRecord.id == query_id,
                QueryRecord.workspace_id == workspace.id,
            )
        )
        if query is None:
            raise ResourceNotFound("QUERY_NOT_FOUND")
        return query

    @staticmethod
    def _workspace_response(workspace: Workspace) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            created_at=workspace.created_at,
        )

    @staticmethod
    def _query_response(query: QueryRecord) -> QueryResponse:
        return QueryResponse(
            id=query.id,
            workspace_id=query.workspace_id,
            question=query.question,
            created_at=query.created_at,
            attempts=[
                AttemptResponse(
                    id=attempt.id,
                    attempt_number=attempt.attempt_number,
                    retry_of_attempt_id=attempt.retry_of_attempt_id,
                    status=attempt.status,
                    candidate_sql=attempt.candidate_sql,
                    failure_code=attempt.failure_code,
                    result=(json.loads(attempt.result_json) if attempt.result_json else None),
                    created_at=attempt.created_at,
                )
                for attempt in query.attempts
            ],
        )
