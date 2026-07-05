"""Email tools. The sender is a mock that never sends real email."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agentpatrol.tool import BaseTool, SideEffectLevel


class EmailArgs(BaseModel):
    to: list[str] = Field(default_factory=list)
    subject: str
    body: str


class EmailDrafterTool(BaseTool):
    name = "email_drafter"
    description = "Create a draft email object (no sending)."
    args_schema = EmailArgs
    side_effect_level = SideEffectLevel.LOW

    def run(self, args: EmailArgs) -> dict[str, Any]:  # type: ignore[override]
        return {
            "status": "drafted",
            "to": args.to,
            "subject": args.subject,
            "body": args.body,
        }


class EmailSenderTool(BaseTool):
    name = "email_sender"
    description = "Mock email sender. Logs the proposed send but never sends."
    args_schema = EmailArgs
    side_effect_level = SideEffectLevel.HIGH

    def run(self, args: EmailArgs) -> dict[str, Any]:  # type: ignore[override]
        return {
            "status": "logged_not_sent",
            "to": args.to,
            "subject": args.subject,
            "note": "Agent Patrol never sends real email; this send was recorded only.",
        }
