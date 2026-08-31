from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.analytics import (
    QueryExecutor,
    SqliteReadOnlyQueryExecutor,
    initialize_synthetic_analytics_db,
)
from app.api import router
from app.config import Settings
from app.database import Database
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
    initialize_default_analytics = executor is None

    resolved_executor: QueryExecutor = executor or SqliteReadOnlyQueryExecutor(
        database_path=resolved_settings.analytics_database_path,
        max_result_rows=resolved_settings.max_result_rows,
        timeout_seconds=resolved_settings.query_timeout_seconds,
    )

    service = Text2SqlWorkspaceService(
        database=database,
        model=resolved_model,
        validator=SqlPolicyValidator(allowed_tables=ALLOWED_ANALYTICS_TABLES),
        executor=resolved_executor,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if initialize_default_analytics:
            initialize_synthetic_analytics_db(resolved_settings.analytics_database_path)
        service.initialize()
        yield

    application = FastAPI(
        title="Text2SQL Workspace",
        description="Multi-user LLM Data Query Service",
        version="0.2.0",
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.service = service
    application.include_router(router)

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "UP"}

    return application


app = create_app()
