.PHONY: clean clean-build clean-pyc clean-test initdb test venv help
.DEFAULT_GOAL := help

DB_FILE := bl_sparfa_server

clean: clean-build clean-pyc clean-test

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

.venv:
	python3 -m venv .venv && \
		source .venv/bin/activate && \
		cd ../biglearn-sparfa-algs && \
		pip install -e . && \
		cd - && \
		pip install -e .

initdb: .venv
	. .env && \
	psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	-c "DROP USER IF EXISTS $${PG_USER}" && \
	psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	-c "CREATE USER $${PG_USER} WITH SUPERUSER PASSWORD '$${PG_PASSWORD}'" && \
	psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U $${PG_USER} \
	-c "DROP DATABASE IF EXISTS $${PG_DB}" && \
	psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	-c "CREATE DATABASE $${PG_DB} ENCODING 'UTF8'" && \
	xz -d -k dev/$(DB_FILE).sql.xz && \
	psql -h $${PG_HOST} -p $${PG_PORT} -d $${PG_DB} -U $${PG_USER} -v ON_ERROR_STOP=1 -1 \
	-f dev/$(DB_FILE).sql && \
	alembic upgrade head
	rm dev/$(DB_FILE).sql

test: .venv
	. .env && python3 setup.py test

venv: .venv

help:
	@echo "The following targets are available:"
	@echo "clean       Remove build, file, and test artifacts"
	@echo "clean-build Remove build artifacts"
	@echo "clean-pyc   Remove file artifacts"
	@echo "clean-test  Remove test artifacts"
	@echo "initdb      Initialize the database and run migrations"
	@echo "test        Run tests quickly with python3"
	@echo "venv        Initialize the python3 virtualenv"
	@echo "help        Print this list of targets"
