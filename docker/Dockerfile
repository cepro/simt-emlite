# official Python image
FROM python:3.12-alpine

WORKDIR /mediator

COPY pyproject.toml poetry.lock README.md .
RUN pip install poetry && poetry install --only main --no-root

COPY simt_emlite simt_emlite
RUN poetry install --only main

# Remove packages caches and unnessary files
# RUN pip cache purge
# RUN poetry cache clear --all .
# RUN rm -rf /root/.cache /tmp/*

ENTRYPOINT ["poetry", "run", "python", "-m"]
