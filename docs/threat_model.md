# Threat model

Agent Patrol addresses risks that arise when an autonomous agent can call tools.
It is a policy and auditing layer, not a security sandbox.

## Risks considered

- **Prompt injection.** Instructions embedded in data (a document, an email
  body, a database row) may try to steer the agent toward harmful tool calls.
  Agent Patrol does not trust the origin of a proposed call: the same policies
  apply whether a call came from a benign plan or an injected instruction. An
  injected "email the API key to this address" is blocked by the same secret
  detection as any other send.
- **Excessive agency.** An agent may take more or larger actions than intended.
  Rate limiting caps repeated calls, and side-effecting actions (sending email,
  writing files, creating events) require review rather than executing freely.
- **Sensitive data exposure.** Secret and PII detection block or review calls
  that would move credentials or personal data through a side-effecting tool.
  SQL queries that reference sensitive fields are blocked.
- **Unsafe tool use.** Destructive shell commands and non-SELECT SQL are
  blocked outright, with the tools themselves re-checking at execution time.
- **Insecure tool design.** Every tool declares a typed argument schema; calls
  that do not validate never reach a policy or an execution path.
- **Malformed outputs.** Tools return structured results and optionally declare
  an output schema; validation failures are recorded in the trace.

## What Agent Patrol does not protect against

- It is **not a sandbox**. The shell tool is a mock and the file tools rely on
  path checks, not OS-level isolation. Do not point the file tools at a
  sensitive filesystem and assume containment.
- Detection is **pattern-based**. Regex secret/PII detection and keyword-based
  SQL/shell classification are conservative but incomplete; they can miss
  obfuscated inputs and can over-trigger.
- It does not defend the **model or the host** against compromise, supply-chain
  attacks, or side channels.
- It is **not a substitute for a production security review**. It is a
  demonstration of a defensible design, meant to be extended.
