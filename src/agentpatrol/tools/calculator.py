"""Calculator tool built on safe AST evaluation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agentpatrol.detectors import safe_arithmetic
from agentpatrol.tool import BaseTool, SideEffectLevel


class CalculatorArgs(BaseModel):
    expression: str


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate a numeric arithmetic expression."
    args_schema = CalculatorArgs
    side_effect_level = SideEffectLevel.NONE

    def run(self, args: CalculatorArgs) -> dict[str, Any]:  # type: ignore[override]
        return {"expression": args.expression, "result": safe_arithmetic(args.expression)}
