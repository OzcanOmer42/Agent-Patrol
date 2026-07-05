"""Policy governing SQL query tools."""

from __future__ import annotations

from agentpatrol.decisions import PolicyDecision
from agentpatrol.detectors import classify_sql
from agentpatrol.policies.base import Policy, PolicyContext, PolicyResult
from agentpatrol.tool import BaseTool, ToolCall

SQL_TOOLS = {"sql_query"}


class SQLPolicy(Policy):
    """Conservative allow-list for read-only SQL."""

    name = "sql_policy"

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        if call.tool_name not in SQL_TOOLS:
            return self.allow()

        query = str(call.args.get("query", ""))
        if not query.strip():
            return self.result(PolicyDecision.BLOCK, "empty query", 0.6)

        cfg = context.config.sql
        assessment = classify_sql(query, sensitive_fields=tuple(cfg.sensitive_fields))

        if assessment.multi_statement:
            return self.result(
                PolicyDecision.BLOCK, "multiple statements are not allowed", 0.9
            )
        if assessment.has_write_keyword or not assessment.is_select:
            keywords = ", ".join(assessment.forbidden_keywords) or "non-SELECT statement"
            return self.result(
                PolicyDecision.BLOCK, f"write/DDL statement rejected ({keywords})", 0.95
            )
        if assessment.touches_sensitive_field:
            return self.result(
                PolicyDecision.BLOCK, "query references a sensitive field", 0.9
            )

        unknown_tables = [t for t in assessment.tables if t not in set(cfg.allowed_tables)]
        if unknown_tables:
            return self.result(
                PolicyDecision.REVIEW,
                f"query touches unapproved table(s): {', '.join(unknown_tables)}",
                0.5,
            )
        if assessment.limit is not None and assessment.limit > cfg.large_limit_threshold:
            return self.result(
                PolicyDecision.REVIEW,
                f"result limit {assessment.limit} exceeds threshold",
                0.4,
            )
        if assessment.is_select_star:
            return self.result(
                PolicyDecision.WARN, "broad SELECT * query", 0.2
            )

        return self.allow("read-only SELECT on approved tables")
