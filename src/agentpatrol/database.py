"""SQLite helpers for the demo database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT
);
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    customer_email TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    due_date TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    total REAL NOT NULL,
    created_at TEXT NOT NULL
);
"""

_CUSTOMERS = [
    (1, "Acme Corp", "billing@acme.example", "415-555-0100"),
    (2, "Globex", "ap@globex.example", "415-555-0111"),
    (3, "Initech", "finance@initech.example", "415-555-0122"),
]

_INVOICES = [
    (1, 1, "billing@acme.example", 1200.0, "overdue", "2025-01-15"),
    (2, 2, "ap@globex.example", 640.5, "paid", "2025-02-01"),
    (3, 3, "finance@initech.example", 980.0, "overdue", "2025-01-20"),
    (4, 1, "billing@acme.example", 220.0, "open", "2025-03-05"),
]

_ORDERS = [
    (1, 1, "Widget", 10, 250.0, "2025-01-02"),
    (2, 2, "Gadget", 4, 400.0, "2025-01-08"),
    (3, 3, "Sprocket", 25, 375.0, "2025-01-11"),
]


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Return a SQLite connection with row access by column name."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def seed_database(db_path: str | Path) -> Path:
    """Create the schema and insert demo rows (idempotent)."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(path)
    try:
        conn.executescript(_SCHEMA)
        conn.execute("DELETE FROM customers")
        conn.execute("DELETE FROM invoices")
        conn.execute("DELETE FROM orders")
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", _CUSTOMERS)
        conn.executemany("INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?)", _INVOICES)
        conn.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", _ORDERS)
        conn.commit()
    finally:
        conn.close()
    return path
