# Architecture

Agent Patrol sits between an agent and the tools it wants to call. The agent
proposes tool calls; Agent Patrol decides whether each one runs.

## Runtime flow

```
                 +-------------------+
  user task ---> |     MockAgent     |  proposes tool calls
                 +-------------------+
                          |
                          v
                 +-------------------+
                 | Schema validation |  args must match the tool's Pydantic schema
                 +-------------------+
                          | valid                    | invalid
                          v                          v
                 +-------------------+          decision = BLOCK
                 |   Policy engine   |
                 |  (all policies)   |
                 +-------------------+
                          |
             most severe of all policy decisions
             BLOCK > REVIEW > WARN > ALLOW
                          |
          +---------------+----------------+
          |        |            |          |
        ALLOW     WARN        REVIEW      BLOCK
          |        |            |          |
       execute  execute   approved? --no--> skip
          |        |         |
          |        |        yes -> execute
          +--------+---------+
                   |
                   v
          +-------------------+
          |   Trace logging   |  JSONL, one record per run
          +-------------------+
                   |
                   v
             final RunReport
```

## Modules

- `decisions.py` - the `PolicyDecision` enum and the conservative aggregation
  rule (`worst_decision`). No third-party dependencies.
- `detectors.py` - pure detection helpers: SQL classification, shell command
  classification, secret/PII detection, safe arithmetic, and path safety. This
  is where the safety-critical string analysis lives, kept separate so it is
  small and directly testable.
- `tool.py` / `registry.py` - the `BaseTool` abstraction, the `ToolCall` model,
  and the registry that validates calls against tool schemas.
- `policy.py` - `PolicyResult`, `PolicyContext`, the `Policy` base class, and
  the `PolicyEngine` that aggregates results.
- `policies/` - the concrete policies (SQL, shell, email, file, calendar, PII,
  rate limit).
- `tools/` - the concrete tools. Side-effecting tools (email sender, shell) are
  mocked or sandboxed.
- `agent.py` - the deterministic `MockAgent`.
- `runtime.py` - `AgentPatrolRuntime`, which orchestrates the flow above.
- `evaluator.py` - scores labelled scenarios and computes metrics.
- `trace.py` - the JSONL trace store and models.
- `config.py` - typed configuration loaded from YAML.
- `api.py` - the FastAPI surface.
- `cli.py` - the argparse command-line interface used by `scripts/`.

## Why this shape

The interesting properties of the system are validation, policy aggregation,
auditability, and evaluation, not plan quality. Keeping the agent behind a
narrow `plan(task) -> list[ToolCall]` interface means the deterministic
`MockAgent` can be replaced by an LLM planner without touching the rest of the
pipeline.
