from agentpatrol.decisions import PolicyDecision as D


def test_select_on_approved_table_allowed(decide):
    assert decide("sql_query", {"query": "SELECT id, amount FROM invoices LIMIT 5"}) is D.ALLOW


def test_drop_table_blocked(decide):
    assert decide("sql_query", {"query": "DROP TABLE customers"}) is D.BLOCK


def test_delete_blocked(decide):
    assert decide("sql_query", {"query": "DELETE FROM invoices WHERE 1=1"}) is D.BLOCK


def test_stacked_query_blocked(decide):
    assert decide("sql_query", {"query": "SELECT * FROM invoices; DROP TABLE invoices"}) is D.BLOCK


def test_sensitive_field_blocked(decide):
    assert decide("sql_query", {"query": "SELECT password FROM customers"}) is D.BLOCK


def test_select_star_warns(decide):
    assert decide("sql_query", {"query": "SELECT * FROM orders"}) is D.WARN


def test_unknown_table_reviews(decide):
    assert decide("sql_query", {"query": "SELECT id FROM audit_log LIMIT 5"}) is D.REVIEW
