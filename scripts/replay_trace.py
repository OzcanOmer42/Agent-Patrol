"""Print a readable timeline for a previous run."""

import argparse

from agentpatrol.cli import cmd_replay
from agentpatrol.trace import DEFAULT_TRACE_PATH

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay an AgentPatrol trace")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--trace", default=DEFAULT_TRACE_PATH)
    args = parser.parse_args()
    cmd_replay(args.run_id, args.trace)
