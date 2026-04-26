.PHONY: lint test build up down smoke

lint:
	python3 tools/lint.py

test:
	python3 -m unittest discover -s tests -p "test_*.py"

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

smoke:
	docker exec avito-ocr-app python tools/smoke_test.py
