FROM python:3.12.10-alpine

WORKDIR /mediator

COPY pyproject.toml poetry.lock README.md .
RUN pip install poetry && poetry install --only main --no-root

COPY simt_emlite simt_emlite

# Remove packages caches and unnessary files (fails ... needs investigtion)
# RUN pip cache purge
# RUN poetry cache clear --all .
# RUN rm -rf /root/.cache /tmp/*

ENTRYPOINT ["poetry", "run", "python", "-m"]
