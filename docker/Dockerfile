# official Python image
FROM python:3.12-alpine

WORKDIR /mediator

COPY pyproject.toml poetry.lock .
RUN pip install poetry && poetry install --only main --no-root
COPY emlite_mediator emlite_mediator
RUN poetry install --only main

ENTRYPOINT ["python", "-m"]
