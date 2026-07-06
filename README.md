# Agent Patrol

**Validate, govern, and trace every agent action.**

Agent Patrol is a lightweight Python runtime for safer tool-using AI agents. It
places a validation and policy layer between an agent and its tools, so every
proposed action is checked before execution. Each tool call receives an
auditable decision: allow, warn, block, or require human review.

## Overview

Most agent demos let a model call tools directly. Agent Patrol inserts a checkpoint
in front of the tools:

```
user task -> agent -> proposed tool call -> schema validation -> policy engine
          -> decision (ALLOW / WARN / BLOCK / REVIEW) -> optional approval
          -> tool execution -> trace logging -> report
```

The MVP uses a deterministic mock agent so behaviour is reproducible and
testable. The agent is hidden behind a narrow `plan(task) -> list[ToolCall]`
interface, so a real LLM planner can replace it without changing the rest of the
pipeline.

## Why Agent Patrol

- **Fail-closed by construction.** Policies combine conservatively
  (`BLOCK > REVIEW > WARN > ALLOW`); a call runs only if every policy allows it.
  Adding a policy can only make the system stricter.
- **Typed at the boundary.** Every tool declares a Pydantic argument schema.
  Calls that do not validate never reach an execution path.
- **Auditable.** Every run produces a replayable JSONL trace with the decision,
  the deciding policy, the reason, a risk score, and latency for each step.
- **Measured, not asserted.** A scenario suite and evaluator report accuracy and
  a false-allow rate computed from the real policies.
- **Runs locally.** No paid APIs or network calls are required.

## Core features

- Four-way decisions with conservative aggregation and per-policy explanations.
- Seven policies: SQL, shell, email, file, calendar, PII/secret, and rate limit.
- Nine tools, with side-effecting ones (email send, shell) mocked or sandboxed.
- Human-in-the-loop review with an explicit approval path.
- Replayable execution traces.
- An evaluation harness with labelled scenarios and safety metrics.
- A FastAPI surface and a small CLI.

## Architecture

```
                 +-------------------+
  user task ---> |     MockAgent     |
                 +-------------------+
                          v
                 +-------------------+       invalid
                 | Schema validation | -------------> BLOCK
                 +-------------------+
                          v (valid)
                 +-------------------+
                 |   Policy engine   |  most severe of all policy decisions
                 +-------------------+
                          v
        ALLOW / WARN --> execute      REVIEW --> approve? --> execute or skip
        BLOCK --------> never runs
                          v
                 +-------------------+
                 |   Trace logging   |  JSONL, one record per run
                 +-------------------+
```

See [docs/architecture.md](docs/architecture.md) for the module map.

## Quickstart

```bash
# from a fresh clone
make install                 # pip install -e ".[dev]"
make seed                    # create the demo SQLite database
make test                    # run the test suite
make eval                    # run the evaluation and print metrics
make api                     # start the API at http://127.0.0.1:8000
```

Requires Python 3.11+.

## Example demo

```bash
python scripts/run_demo.py --task examples/risky_email_task.json
```

```
Task: Find overdue invoices and send reminder emails to customers.

[ALLOW ] sql_query       executed  all policies allow
[ALLOW ] email_drafter   executed  all policies allow
[REVIEW] email_sender    skipped   email_policy: sending email requires review

Summary: {'allow': 2, 'warn': 0, 'review': 1, 'block': 0, 'executed': 2}
```

The email send is held for review. Re-run with `--approve-review` to approve it;
the trace records whether review was approved or skipped. Other examples show
BLOCK behaviour:

```bash
python scripts/run_demo.py --task examples/shell_delete_task.json   # rm -rf -> BLOCK
python scripts/run_demo.py --task examples/sql_injection_task.json  # stacked query -> BLOCK
```

Replay any run:

```bash
python scripts/replay_trace.py --run-id <run_id>
```

## Policy decisions

| Decision | Meaning | Executes? |
| --- | --- | --- |
| ALLOW | safe | yes |
| WARN | allowed but flagged | yes |
| REVIEW | needs human approval | only if approved |
| BLOCK | never | no |

Policy behaviour is documented in [docs/policy_design.md](docs/policy_design.md).

## Tools included

| Tool | Side effect | Notes |
| --- | --- | --- |
| `calculator` | none | safe AST arithmetic, no `eval` |
| `file_reader` | low | reads inside allowed directories only |
| `file_writer` | medium | writes into the workspace; requires review |
| `sql_query` | low | SELECT-only over the demo SQLite database |
| `email_drafter` | low | builds a draft |
| `email_sender` | high | mock; logs the send, never sends |
| `calendar_reader` | none | mock events |
| `calendar_writer` | medium | mock; requires review |
| `shell_command` | high | sandboxed mock; simulates whitelisted commands only |

## Evaluation

```bash
python scripts/run_eval.py
```

On the bundled 39-scenario suite the current policies score:

```
policy_accuracy                 : 1.000
false_allow_rate                : 0.000
false_block_rate                : 0.000
review_precision                : 1.000
schema_validation_failure_count : 4
```

`false_allow_rate` is the safety-critical metric (dangerous actions that were
allowed). Metrics are computed from real evaluations; see
[docs/evaluation.md](docs/evaluation.md).

## API usage

```bash
uvicorn agentpatrol.api:app --reload
```

A browser console is served at **`http://127.0.0.1:8000/ui`**: pick a scenario or edit
the task payload, run an inspection, and watch each proposed tool call get a colour-coded
allow / warn / block / review verdict. It also lists the registered tools and active
policies and can run the evaluation suite on demand.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | project status |
| GET | `/ui` | browser console (dashboard) |
| GET | `/tools` | list registered tools |
| GET | `/policies` | list active policies |
| POST | `/run` | run a task through the runtime |
| GET | `/traces/{run_id}` | fetch a run trace |
| POST | `/evaluate` | run the evaluation suite |

```bash
curl -s http://127.0.0.1:8000/run -H 'content-type: application/json' -d '{
  "task": "cleanup",
  "tool_calls": [{"tool_name": "shell_command", "args": {"command": "rm -rf /"}}]
}'
```

## Repository structure

```
src/agentpatrol/
  decisions.py      # decision enum + conservative aggregation
  detectors.py      # pure SQL/shell/secret/PII/path/arithmetic helpers
  tool.py           # BaseTool, SideEffectLevel, ToolCall
  registry.py       # tool registry
  validators.py     # schema-validation helpers
  policy.py         # PolicyResult, PolicyContext, PolicyEngine
  policies/         # sql, shell, email, file, calendar, pii, rate_limit
  tools/            # calculator, file, sql, email, calendar, shell
  agent.py          # deterministic MockAgent
  runtime.py        # AgentPatrolRuntime
  evaluator.py      # scenario scoring + metrics
  trace.py          # JSONL trace store
  config.py         # typed config from YAML
  api.py            # FastAPI app
  cli.py            # argparse CLI
configs/            # default and strict policy YAML
scripts/            # seed, demo, eval, replay entry points
examples/           # task files + eval_scenarios.json
tests/              # pytest suite
docs/               # architecture, policy design, evaluation, threat model, limitations
```

## Testing

```bash
make test            # pytest
make lint            # ruff check
```

Tests cover tool registration, schema validation, each policy, engine priority,
trace round-tripping, evaluator metric math, and the API endpoints. CI runs ruff
and pytest on Python 3.11 and 3.12.

## Design tradeoffs

- **Deterministic agent over model quality.** The value here is validation,
  policy enforcement, tracing, and evaluation, so the agent is intentionally a
  fixed mapping. This keeps the project reproducible and testable.
- **Pure detection layer.** SQL/shell/PII analysis lives in a dependency-free
  module separate from the framework code, so the safety-critical logic is small
  and unit-testable in isolation.
- **Allow-list and fail-closed.** Conservative choices (SELECT-only SQL, command
  whitelists, review-by-default for side effects) favour safety over
  convenience, and can be relaxed through config.
- **File-based traces.** JSONL keeps traces human-readable and trivial to
  replay, at the cost of concurrency and retention features.

## Limitations

The shell tool is a mock, detection is pattern-based, the agent is
deterministic, and SQL parsing is conservative and incomplete. Agent Patrol is a
policy and auditing layer, not a security sandbox, and is not a substitute for a
production security review. See [docs/limitations.md](docs/limitations.md) and
[docs/threat_model.md](docs/threat_model.md).

## Future work

- Swap `MockAgent` for a real LLM planner behind the same interface.
- Replace regex detection with a stronger secret/PII detector.
- Use a real SQL parser and a proper execution sandbox.
- Move traces to a database with retention and search.
- Grow the evaluation suite toward adversarial coverage.

## Resume bullets

- Built Agent Patrol, a Python runtime that places a typed validation and policy
  layer between a tool-using agent and its tools, producing an auditable
  allow/warn/block/review decision for every action.
- Designed seven composable policies with fail-closed aggregation
  (BLOCK > REVIEW > WARN > ALLOW) and defense-in-depth execution checks; scored
  them with an evaluation harness reporting accuracy and a false-allow rate.
- Implemented replayable JSONL execution traces, a FastAPI service, a CLI, and a
  pytest/ruff/GitHub Actions setup across Python 3.11 and 3.12.

## License

MIT. See [LICENSE](LICENSE).
