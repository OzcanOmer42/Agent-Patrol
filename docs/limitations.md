# Limitations

This project is deliberately scoped as a clean, working core rather than a
hardened product. The main limitations:

- **No real sandbox.** The shell tool never executes real commands; it simulates
  a handful of harmless ones. The file tools use resolved-path checks, not OS
  isolation. This is safe for the demo but is not a containment boundary.
- **Deterministic mock agent.** The MVP maps tasks to tool calls with fixed
  rules and explicit `tool_calls` in example files. It does not use a real
  model, so plans are predictable by design.
- **Regex-based PII/secret detection.** Detection is conservative and
  incomplete. It will miss obfuscated secrets and can produce false positives on
  ordinary text.
- **Keyword-based SQL analysis.** SQL classification uses keyword and structure
  heuristics, not a full parser. It is intentionally strict (only single
  `SELECT` statements pass) and may reject valid-but-unusual queries.
- **Single-process, file-based traces.** Traces are appended to a JSONL file.
  There is no concurrency control, retention policy, or database-backed store.
- **No authentication or multi-tenant model.** The API runs a single shared
  runtime with no auth; it is meant for local use and demos.
- **Evaluation is a curated suite.** The scenario set demonstrates intended
  behaviour on a fixed set of cases; it is not an adversarial benchmark.

None of these are hidden: the design favours a small, auditable core that is
easy to reason about and extend. Hardening any one of them (a real sandbox, a
proper SQL parser, an ML-based detector, a database trace store) is a natural
next step.
