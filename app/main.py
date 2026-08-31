from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.analytics import (
    PostgresReadOnlyQueryExecutor,
    QueryExecutor,
    SqliteReadOnlyQueryExecutor,
    initialize_synthetic_analytics_db,
)
from app.api import router
from app.config import Settings
from app.database import Database
from app.evaluation import EvaluationRunner
from app.service import Text2SqlWorkspaceService
from app.sql_policy import SqlPolicyValidator
from app.text2sql import FixtureText2SqlModel, Text2SqlModel


ALLOWED_ANALYTICS_TABLES = {"customers", "products", "orders", "order_items"}


def create_app(
    *,
    settings: Settings | None = None,
    model: Text2SqlModel | None = None,
    executor: QueryExecutor | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    database = Database(resolved_settings.metadata_database_url)
    resolved_model = model or FixtureText2SqlModel()
    initialize_default_sqlite = False

    if executor is not None:
        resolved_executor = executor
    elif resolved_settings.analytics_database_url:
        resolved_executor = PostgresReadOnlyQueryExecutor(
            dsn=resolved_settings.analytics_database_url,
            max_result_rows=resolved_settings.max_result_rows,
            timeout_seconds=resolved_settings.query_timeout_seconds,
        )
    else:
        initialize_default_sqlite = True
        resolved_executor = SqliteReadOnlyQueryExecutor(
            database_path=resolved_settings.analytics_database_path,
            max_result_rows=resolved_settings.max_result_rows,
            timeout_seconds=resolved_settings.query_timeout_seconds,
        )

    validator = SqlPolicyValidator(allowed_tables=ALLOWED_ANALYTICS_TABLES)

    service = Text2SqlWorkspaceService(
        database=database,
        model=resolved_model,
        validator=validator,
        executor=resolved_executor,
    )
    evaluation_runner = EvaluationRunner(
        model=resolved_model,
        validator=validator,
        executor=resolved_executor,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if initialize_default_sqlite:
            initialize_synthetic_analytics_db(resolved_settings.analytics_database_path)
        service.initialize()
        yield

    application = FastAPI(
        title="Text2SQL Workspace",
        description="Multi-user LLM Data Query Service",
        version="0.4.0",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.service = service
    application.state.evaluation_runner = evaluation_runner
    application.include_router(router)

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "UP"}

    return application


app = create_app()
