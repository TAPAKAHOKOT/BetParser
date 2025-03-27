start:
	uvicorn main:app --reload

pre-commit:
	pre-commit install

lint:
	ruff check . --fix

format:
	ruff format
