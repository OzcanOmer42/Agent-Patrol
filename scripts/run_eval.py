"""Run all evaluation scenarios and print metrics."""

import argparse

from agentpatrol.cli import cmd_eval
from agentpatrol.tools import DEFAULT_DB_PATH

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AgentPatrol evaluation")
    parser.add_argument("--scenarios", default="examples/eval_scenarios.json")
    parser.add_argument("--config", default=None)
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    cmd_eval(args.scenarios, args.config, args.db)
