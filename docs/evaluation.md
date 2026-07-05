# Evaluation

Agent Patrol ships with a labelled scenario set and a harness that scores the
policy engine against it. The metrics are computed from real evaluations of the
implemented policies; nothing is hard-coded.

## Dataset

`examples/eval_scenarios.json` contains scenarios, each with a `name`,
`tool_name`, `args`, `expected_decision`, and `category`. Categories:

- `safe_read`, `safe_query` - actions that should be allowed (or warned).
- `risky_email` - email sends that should require review.
- `destructive_shell` - dangerous commands that should be blocked.
- `sensitive_file` - credential/out-of-scope file access that should be blocked.
- `sql_injection` - writes, stacked statements, and sensitive-field reads.
- `pii_leakage` - secrets or PII, scaled by side-effect level.
- `malformed_args` - argument sets that fail schema validation.
- `excessive_tool_calls` - repeated calls that trip the rate limit.
- `prompt_injection_like_instruction` - instruction-shaped payloads whose
  effect still routes through the same policies.

A scenario may include a `context` block (for example `{"call_count": 5}`) to
simulate repeated calls within a run.

## Metrics

- `policy_accuracy` - fraction of scenarios where the decision matched the
  expected label.
- `false_allow_rate` - of scenarios that should have been restricted (expected
  anything other than ALLOW), the fraction that were nonetheless allowed. This
  is the safety-critical metric: it measures dangerous actions that slipped
  through.
- `false_block_rate` - of scenarios that should have been allowed, the fraction
  that were blocked. This measures over-blocking of legitimate actions.
- `review_precision` - of the scenarios the engine sent to review, the fraction
  that were expected to be reviewed.
- `schema_validation_failure_count` - how many scenarios failed schema
  validation (these are treated as blocked).
- `average_policy_latency_ms` - mean time to evaluate the policy engine per
  scenario that reached it.

## Running

```bash
python scripts/run_eval.py
# or
make eval
```

The harness prints the metrics, a per-category correct/total breakdown, and any
mismatches so regressions are easy to spot when policies change.
