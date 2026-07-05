"""SQL query tool over the demo SQLite database."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from agentpatrol.detectors import classify_sql
from agentpatrol.tool import BaseTool, SideEffectLevel

_MAX_ROWS = 100


class SqlQueryArgs(BaseModel):
    query: str


class SqlQueryTool(BaseTool):
    name = "sql_query"
    description = "Run a read-only SELECT query against the demo database."
    args_schema = SqlQueryArgs
    side_effect_level = SideEffectLevel.LOW

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)

    def run(self, args: SqlQueryArgs) -> dict[str, Any]:  # type: ignore[override]
        # Defense in depth: even if a policy allowed this, refuse anything
        # that is not a single read-only SELECT at execution time.
        assessment = classify_sql(args.query)
        if not assessment.is_select or assessment.has_write_keyword or assessment.multi_statement:
            raise ValueError("execution refused: only single-statement SELECT is permitted")

        # Local import keeps the SQLite connection out of module import time.
        from agentpatrol.database import get_connection

        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(args.query)
            rows = [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
        return {"row_count": len(rows), "rows": rows[:_MAX_ROWS]}
