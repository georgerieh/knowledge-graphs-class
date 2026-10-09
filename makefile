.PHONY: help run docker-build docker-run test clean venv install lint format tree

TAG ?= graph-api:dev

help:
	@echo "Commands:"
	@echo "  make venv           Create local virtualenv (.venv)"
	@echo "  make install        Install requirements into .venv"
	@echo "  make run            Run FastAPI (uvicorn) on :8000"
	@echo "  make docker-build   Build Docker image (TAG=$(TAG))"
	@echo "  make docker-run     Start the Docker Compose stack"
	@echo "  make test           Run pytest suite"
	@echo "  make lint           Run pylint"
	@echo "  make format         Run black code formatter"
	@echo "  make clean          Remove caches and temp files"
	@echo "  make tree           Show project tree (depth 3)"

venv:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		. .venv/bin/activate && pip install --upgrade pip; \
		echo "Created .venv"; \
	else echo ".venv already exists"; fi
	@echo "To activate: source .venv/bin/activate"

install: venv
	@. .venv/bin/activate && pip install -r requirements.txt

run:
	@. .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker compose build

docker-run:
	docker compose up --build

test:
	@. .venv/bin/activate && pytest -q --cov=app --cov-report=term-missing

lint:
	@. .venv/bin/activate && pylint app

format:
	@. .venv/bin/activate && black app -l 120

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} \; || true
	find . -type f -name "*.pyc" -delete || true

tree:
	@if command -v tree >/dev/null 2>&1; then \
		tree -L 3 -I "node_modules|dist|.git|.venv|__pycache__"; \
	else find . -maxdepth 3 -type d -not -path '*/\.*' | sort; fi
