FROM python:3.11-slim
WORKDIR /code

# First copy just the dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Then copy the rest of the application
COPY app ./app

CMD ["flask", "--app", "manage.py", "run", "--host", "0.0.0.0", "--port", "8000"]