.PHONY: train test run docker

train:
	python build.py

test:
	pytest

run:
	uvicorn app:app --reload

docker:
	docker build -t retention-intelligence .
