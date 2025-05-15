FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade pip && pip install uv

COPY pyproject.toml .
RUN uv venv && uv sync

COPY . .
