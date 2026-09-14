.PHONY: setup format lint typecheck test coverage security eval check

setup:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

format:
	ruff format .

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest

coverage:
	pytest --cov --cov-report=term-missing

security:
	@echo "Security checks will be added in Phase 3."

eval:
	@echo "Evaluation framework will be added in Phase 4."

check:
	ruff format --check .
	ruff check .
	mypy src
	pytest --cov --cov-report=term-missing
