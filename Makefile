.PHONY: install test lint demo eval api seed

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .

seed:
	python scripts/seed_demo_db.py

demo: seed
	python scripts/run_demo.py --task examples/risky_email_task.json

eval:
	python scripts/run_eval.py

api:
	uvicorn agentpatrol.api:app --reload
