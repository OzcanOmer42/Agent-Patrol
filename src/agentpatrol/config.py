"""Typed configuration for AgentPatrol.

Configuration drives policy thresholds so that ``configs/*.yaml`` files can
tighten or relax behaviour without code changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SqlConfig(BaseModel):
    allowed_tables: list[str] = Field(
        default_factory=lambda: ["invoices", "customers", "orders"]
    )
    sensitive_fields: list[str] = Field(
        default_factory=lambda: ["password", "token", "api_key", "ssn", "secret"]
    )
    large_limit_threshold: int = 1000


class ShellConfig(BaseModel):
    allowed_commands: list[str] = Field(
        default_factory=lambda: ["echo", "pwd", "ls", "cat", "date", "whoami"]
    )


class EmailConfig(BaseModel):
    bulk_recipient_threshold: int = 5


class FileConfig(BaseModel):
    allowed_read_dirs: list[str] = Field(default_factory=lambda: ["examples", "data"])
    allowed_write_dirs: list[str] = Field(default_factory=lambda: ["workspace"])
    blocked_names: list[str] = Field(
        default_factory=lambda: [".env", "id_rsa", "credentials", "secrets"]
    )


class PiiConfig(BaseModel):
    # When PII/secrets are present, the decision escalates with side-effect level.
    block_on_high_side_effect: bool = True


class RateLimitConfig(BaseModel):
    soft_limit: int = 3  # calls beyond this to the same tool require REVIEW
    hard_limit: int = 6  # calls beyond this are BLOCKed


class AgentPatrolConfig(BaseModel):
    """Top-level configuration object."""

    workspace_root: str = "."
    sql: SqlConfig = Field(default_factory=SqlConfig)
    shell: ShellConfig = Field(default_factory=ShellConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    file: FileConfig = Field(default_factory=FileConfig)
    pii: PiiConfig = Field(default_factory=PiiConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)


def load_config(path: str | Path | None = None) -> AgentPatrolConfig:
    """Load configuration from a YAML file, falling back to defaults."""
    if path is None:
        return AgentPatrolConfig()

    import yaml  # local import keeps yaml optional for pure-config usage

    data: dict[str, Any] = yaml.safe_load(Path(path).read_text()) or {}
    return AgentPatrolConfig.model_validate(data)
