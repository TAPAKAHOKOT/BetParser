start:
	uvicorn main:app --reload

pre-commit:
	pre-commit install
