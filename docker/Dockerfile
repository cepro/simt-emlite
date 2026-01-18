FROM python:3.13-alpine

WORKDIR /mediator

COPY pyproject.toml poetry.lock README.md .
RUN pip install poetry && poetry install --only main --no-root

COPY simt_emlite simt_emlite

# Remove packages caches and unnessary files (fails ... needs investigtion)
# RUN pip cache purge
# RUN poetry cache clear --all .
# RUN rm -rf /root/.cache /tmp/*

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["poetry", "run", "python", "-u", "-m"]
