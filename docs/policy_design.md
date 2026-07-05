# Policy design

## Conservative aggregation

Every policy independently returns a `PolicyResult` with one of four decisions.
The engine combines them by taking the most severe:

```
BLOCK > REVIEW > WARN > ALLOW
```

A call is only allowed when every policy allows it. Any single BLOCK blocks the
call; any REVIEW (absent a BLOCK) sends it to human review. This is a
fail-closed design: adding a policy can only make the system stricter, never
more permissive, so policies compose without hidden interactions.

The decisive policies' reasons and risk scores are surfaced on the combined
result, and a full per-policy breakdown is stored in the result metadata and in
the trace, so every decision is explainable after the fact.

## Decision semantics

- `ALLOW` - execute directly.
- `WARN` - execute, but flag the call (for example, a broad `SELECT *`).
- `REVIEW` - do not execute without explicit human approval. In demos, the
  `--approve-review` flag approves reviewed actions so the flow can be seen
  end to end.
- `BLOCK` - never execute.

## Policies

- **SQLPolicy** - allow-list oriented. Only single-statement `SELECT` queries on
  approved tables pass. Writes and DDL (`INSERT`, `UPDATE`, `DELETE`, `DROP`,
  `ALTER`, `TRUNCATE`, ...) and stacked statements are blocked. Queries touching
  sensitive fields are blocked, unapproved tables and oversized limits go to
  review, and broad `SELECT *` queries warn.
- **ShellPolicy** - blocks destructive commands (`rm -rf`, `shutdown`, `kill`,
  `chmod 777`, ...) and commands that read environment variables or secrets;
  reviews network commands (`curl`, `wget`, ...) and anything unrecognised;
  allows a small whitelist of harmless commands.
- **EmailPolicy** - drafting is allowed; sending requires review; content
  containing detected secrets is blocked; bulk sends above a threshold are
  reviewed.
- **FilePolicy** - reads are confined to allowed directories; credential-like
  and hidden files are blocked; writes require review and must stay inside the
  configured workspace.
- **CalendarPolicy** - reading is allowed; creating events requires review.
- **PIIPolicy** - detects secrets and PII in arguments and escalates with the
  tool's side-effect level: the same leaked SSN is blocked for a high
  side-effect tool but only warned for a read-only one.
- **RateLimitPolicy** - caps repeated calls to the same tool within a run:
  beyond a soft limit requires review, beyond a hard limit blocks.

## Defense in depth

Some tools re-check their own preconditions at execution time even though a
policy already vetted the call. The SQL tool refuses anything that is not a
single `SELECT`, and the shell tool only simulates whitelisted commands. A
policy misconfiguration therefore cannot, by itself, cause an unsafe execution.

## Configuration

Thresholds and allow-lists live in `configs/*.yaml` and are loaded into a typed
`AgentPatrolConfig`. `configs/strict_policy.yaml` tightens tables, commands,
limits, and rate caps without any code change.
