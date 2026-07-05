"""Mock calendar tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agentpatrol.tool import BaseTool, SideEffectLevel

_MOCK_EVENTS = [
    {"title": "Standup", "start": "2025-04-01T09:00", "end": "2025-04-01T09:15"},
    {"title": "Design review", "start": "2025-04-01T13:00", "end": "2025-04-01T14:00"},
]


class CalendarReaderArgs(BaseModel):
    date: str | None = None


class CalendarWriterArgs(BaseModel):
    title: str
    start: str
    end: str
    attendees: list[str] = Field(default_factory=list)


class CalendarReaderTool(BaseTool):
    name = "calendar_reader"
    description = "Return mock calendar events."
    args_schema = CalendarReaderArgs
    side_effect_level = SideEffectLevel.NONE

    def run(self, args: CalendarReaderArgs) -> dict[str, Any]:  # type: ignore[override]
        return {"date": args.date, "events": _MOCK_EVENTS}


class CalendarWriterTool(BaseTool):
    name = "calendar_writer"
    description = "Create a mock calendar event."
    args_schema = CalendarWriterArgs
    side_effect_level = SideEffectLevel.MEDIUM

    def run(self, args: CalendarWriterArgs) -> dict[str, Any]:  # type: ignore[override]
        return {
            "status": "created",
            "event": {
                "title": args.title,
                "start": args.start,
                "end": args.end,
                "attendees": args.attendees,
            },
        }
