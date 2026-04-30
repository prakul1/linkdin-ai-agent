.PHONY: install run docker-up docker-down test clean
install:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
run:
	uvicorn app.main:app --reload --port 8000
docker-build:
	docker compose build
docker-up:
	docker compose up -d
docker-down:
	docker compose down
docker-logs:
	docker compose logs -f api
test:
	pytest tests/ -v
clean:
	rm -rf data/chroma data/app.db __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +