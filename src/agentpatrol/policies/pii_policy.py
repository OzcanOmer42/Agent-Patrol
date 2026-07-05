"""Policy detecting PII and secrets in tool arguments."""

from __future__ import annotations

from agentpatrol.decisions import PolicyDecision
from agentpatrol.detectors import SENSITIVE_PII, find_pii, find_secrets
from agentpatrol.policies.base import Policy, PolicyContext, PolicyResult, iter_string_values
from agentpatrol.tool import BaseTool, SideEffectLevel, ToolCall


class PIIPolicy(Policy):
    """Escalates when arguments contain secrets or sensitive PII.

    Severity scales with the tool's side-effect level: the same leaked SSN is
    treated more seriously for a tool that sends data outward than for a
    read-only calculation.
    """

    name = "pii_policy"

    def evaluate(
        self, call: ToolCall, tool: BaseTool, context: PolicyContext
    ) -> PolicyResult:
        text = " ".join(iter_string_values(call.args))
        if not text.strip():
            return self.allow()

        secrets = find_secrets(text)
        pii = find_pii(text)
        sensitive_pii = [p for p in pii if p in SENSITIVE_PII]

        high_side_effect = tool.side_effect_level in (
            SideEffectLevel.MEDIUM,
            SideEffectLevel.HIGH,
        )
        very_high = tool.side_effect_level is SideEffectLevel.HIGH

        if secrets or sensitive_pii:
            labels = ", ".join(secrets + sensitive_pii)
            if very_high and context.config.pii.block_on_high_side_effect:
                return self.result(
                    PolicyDecision.BLOCK, f"secrets/PII with high side effect: {labels}", 0.9
                )
            if high_side_effect:
                return self.result(
                    PolicyDecision.REVIEW, f"secrets/PII detected: {labels}", 0.6
                )
            return self.result(
                PolicyDecision.WARN, f"secrets/PII in low-risk tool: {labels}", 0.3
            )

        low_pii = [p for p in pii if p not in SENSITIVE_PII]
        if low_pii and high_side_effect:
            return self.result(
                PolicyDecision.WARN, f"PII present: {', '.join(low_pii)}", 0.2
            )

        return self.allow()
