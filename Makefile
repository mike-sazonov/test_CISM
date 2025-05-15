DC = docker compose
APP = docker-compose.yaml
ENV = --env-file .env
CONTAINER_APP_NAME = app

.PHONY: lint dev test logs down makemigrations migrate

dev:
	${DC} -f ${APP} ${ENV} up --build -d

down:
	${DC} -f ${APP} down

consumer:
	${DC} -f ${APP} ${ENV} exec ${CONTAINER_APP_NAME} \
	uv run run_consumer.py

logs:
	${DC} -f ${APP} logs -f

makemigrations:
	${DC} -f ${APP} ${ENV} exec ${CONTAINER_APP_NAME} \
	uv run alembic --config alembic.ini revision --autogenerate -m "auto migration"

migrate:
	${DC} -f ${APP} ${ENV} exec ${CONTAINER_APP_NAME} uv run alembic --config alembic.ini upgrade head


test:
	uv run pytest

lint:
	uv run ruff format .
	uv run ruff check --fix .
	uv run mypy .
