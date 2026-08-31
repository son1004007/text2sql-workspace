from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    metadata_database_url: str = "sqlite+pysqlite:///./data/metadata.db"
    analytics_database_path: Path = Path("./data/analytics.db")
    analytics_database_url: str | None = None
    auth_secret: str = "local-demo-secret"
    access_token_ttl_seconds: int = 3600
    max_result_rows: int = 100
    query_timeout_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "Settings":
        analytics_database_url = os.getenv("TEXT2SQL_ANALYTICS_DATABASE_URL")
        return cls(
            metadata_database_url=os.getenv(
                "TEXT2SQL_METADATA_DATABASE_URL",
                "sqlite+pysqlite:///./data/metadata.db",
            ),
            analytics_database_path=Path(
                os.getenv("TEXT2SQL_ANALYTICS_DATABASE_PATH", "./data/analytics.db")
            ),
            analytics_database_url=(
                analytics_database_url.strip() if analytics_database_url else None
            ),
            auth_secret=os.getenv("TEXT2SQL_AUTH_SECRET", "local-demo-secret"),
            access_token_ttl_seconds=int(
                os.getenv("TEXT2SQL_ACCESS_TOKEN_TTL_SECONDS", "3600")
            ),
            max_result_rows=int(os.getenv("TEXT2SQL_MAX_RESULT_ROWS", "100")),
            query_timeout_seconds=float(
                os.getenv("TEXT2SQL_QUERY_TIMEOUT_SECONDS", "1.0")
            ),
        )
