FROM mwalbeck/python-poetry:2.1-3.11

WORKDIR /PostBot

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-root --only main

COPY ../../../../Desktop/PostBot .

CMD ["poetry", "run", "python", "-m", "main"]
