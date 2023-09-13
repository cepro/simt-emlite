# official Python image
FROM python:3.11-alpine

RUN apk add --no-cache git 

WORKDIR /mediator

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY emlite_mediator emlite_mediator

ENTRYPOINT ["python", "-m"]
