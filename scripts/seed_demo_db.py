"""Seed the demo SQLite database with customers, invoices, and orders."""

import argparse

from agentpatrol.cli import cmd_seed
from agentpatrol.tools import DEFAULT_DB_PATH

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the AgentPatrol demo database")
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    cmd_seed(args.db)
