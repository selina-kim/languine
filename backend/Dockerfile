FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.in-project true && \ 
    poetry install --no-root

COPY . .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=src.main:app

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
