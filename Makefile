.PHONY: clean-build clean-pyc clean-test clean env abort-if-production drop-db drop-user drop-all \
	      create-user create-db create-all setup-db setup-all reset-db reset-all test help
.DEFAULT_GOAL := help

clean-build:
	rm -fr .eggs/
	rm -fr build/
	rm -fr dist/
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.egg-info' -exec rm -fr {} +

clean-pyc:
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +

clean-test:
	rm -fr .cache/
	rm -fr .tox/
	rm -f  cov.xml
	rm -fr htmlcov/

clean: clean-build clean-pyc clean-test

.env:
	cp .env.example .env

env: .env

abort-if-production: .env
	if [ -z "$${PY_ENV}" ]; then . ./.env; fi && [ "$${PY_ENV}" != "production" ]

drop-db: .env abort-if-production
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U $${PG_USER} \
	                 -c "DROP DATABASE IF EXISTS $${PG_DB}"

drop-user: .env abort-if-production
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "DROP USER IF EXISTS $${PG_USER}"

drop-all: drop-db drop-user

create-user: .env
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "CREATE USER $${PG_USER} WITH SUPERUSER PASSWORD '$${PG_PASSWORD}'"

create-db: .env
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "CREATE DATABASE $${PG_DB} ENCODING 'UTF8'"

create-all: create-user create-db

setup-db: create-db
	alembic upgrade head

setup-all: create-user setup-db

reset-db: drop-db setup-db

reset-all: drop-all setup-all

test:
	pytest

help:
	@echo "The following targets are available:"
	@echo "clean-build Remove build artifacts"
	@echo "clean-pyc   Remove python artifacts"
	@echo "clean-test  Remove test artifacts"
	@echo "clean       Remove build, python, and test artifacts"
	@echo "drop-db     Drop the database"
	@echo "drop-user   Drop the database user"
	@echo "drop-all    Drop the database and database user"
	@echo "create-user Create the database user"
	@echo "create-db   Create the database"
	@echo "create-all  Create the database user and database"
	@echo "setup-db    Create the database and run all migrations"
	@echo "setup-all   Create the database user and database and run all migrations"
	@echo "reset-db    Drop and recreate the database and run all migrations"
	@echo "reset-all   Drop and recreate the database user and database and run all migrations"
	@echo "test        Run tests using pytest"
	@echo "help        Print this list of targets"
