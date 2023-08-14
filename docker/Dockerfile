# official Python image
FROM python:3.11-slim-bookworm

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /mediator

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY emlite_mediator emlite_mediator

ENTRYPOINT ["python", "-m"]