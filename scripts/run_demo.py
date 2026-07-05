"""Run a task file through the AgentPatrol runtime."""

import argparse

from agentpatrol.cli import cmd_demo
from agentpatrol.tools import DEFAULT_DB_PATH
from agentpatrol.trace import DEFAULT_TRACE_PATH

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an AgentPatrol demo task")
    parser.add_argument("--task", required=True, help="path to a task JSON file")
    parser.add_argument("--approve-review", action="store_true")
    parser.add_argument("--config", default=None)
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    parser.add_argument("--trace", default=DEFAULT_TRACE_PATH)
    args = parser.parse_args()
    cmd_demo(args.task, args.approve_review, args.config, args.db, args.trace)
