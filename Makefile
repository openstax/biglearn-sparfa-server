.PHONY: clean-build clean-pyc clean-test clean env uninstall-python python uninstall-virtualenv \
	      uninstall-venv virtualenv venv install dev-install reset-virtualenv reset-venv \
				requirements freeze update-requirements abort-if-production drop-db drop-user create-user \
				create-db setup-db reset-db test help
.DEFAULT_GOAL := help

PYTHON_VERSION := 3.6.6
VIRTUALENV_NAME := biglearn-sparfa-server

clean-build:
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +

clean-pycache:
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -rf .pytest_cache/
	rm -f .coverage
	rm -f  cov.xml
	rm -rf .tox/

clean: clean-build clean-pycache clean-test

.env:
	cp .env.example .env

env: .env

uninstall-python:
	pyenv uninstall --force ${PYTHON_VERSION}

python:
	pyenv install --skip-existing ${PYTHON_VERSION}

uninstall-virtualenv:
	pyenv uninstall --force ${VIRTUALENV_NAME}
	rm -f .python-version

uninstall-venv: uninstall-virtualenv

virtualenv: python
	pyenv virtualenv --force ${PYTHON_VERSION} ${VIRTUALENV_NAME}
	pyenv local ${VIRTUALENV_NAME}

venv: virtualenv

.python-version:
	make virtualenv

install: .python-version
	pip install -r requirements.txt

dev-install: .python-version install
	pip install -e .[dev]

reset-virtualenv: uninstall-virtualenv virtualenv

reset-venv: reset-virtualenv

requirements: .python-version
	if [ -z "$$(pip freeze)" ]; then make install; fi
	echo "$$(pip freeze)" | \
	sed -e 's/-e git+https:\/\/github.com\/openstax\/biglearn-sparfa-server\.git@[0-9a-f]*#egg=sparfa_server/-e ./' > requirements.txt

freeze: requirements

update-requirements: reset-virtualenv
	pip install -e git+https://github.com/openstax/biglearn-sparfa-algs#egg=sparfa_algs
	pip install -e .
	make requirements

abort-if-production: .env
	if [ -z "$${PY_ENV}" ]; then . ./.env; fi && [ "$${PY_ENV}" != "production" ]

drop-db: .env abort-if-production
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U $${PG_USER} \
	                 -c "DROP DATABASE IF EXISTS $${PG_DB}"

drop-user: .env abort-if-production
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "DROP USER IF EXISTS $${PG_USER}"

create-user: .env
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "CREATE USER $${PG_USER} WITH SUPERUSER PASSWORD '$${PG_PASSWORD}'"

create-db: .env
	. ./.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "CREATE DATABASE $${PG_DB} ENCODING 'UTF8'"

setup-db: .python-version create-db
	alembic upgrade head

reset-db: drop-db setup-db

test: .env dev-install
	pytest
	pycodestyle

help:
	@echo "The following targets are available:"
	@echo "clean-build            Remove build artifacts"
	@echo "clean-pycache          Remove pycache artifacts"
	@echo "clean-test             Remove test artifacts"
	@echo "clean                  Remove build, python, and test artifacts"
	@echo "[.]env                 Copy .env.example into .env"
	@echo "uninstall-python       Uninstall Python ${PYTHON_VERSION} using pyenv"
	@echo "python                 Install Python ${PYTHON_VERSION} using pyenv"
	@echo "uninstall-v[irtual]env Uninstall the ${VIRTUALENV_NAME} virtualenv using pyenv-virtualenv"
	@echo "v[irtual]env           Create the ${VIRTUALENV_NAME} virtualenv using pyenv-virtualenv"
	@echo "install                Install requirements using versions from requirements.txt"
	@echo "dev-install            Install dev requirements listed in setup.py"
	@echo ".python-version        Create the virtualenv only if .python-version does not yet exist"
	@echo "reset-v[irtual]env     Recreate the ${VIRTUALENV_NAME} virtualenv using pyenv-virtualenv"
	@echo "requirements/freeze    Create requirements.txt based on package versions currently installed in the ${VIRTUALENV_NAME} virtualenv"
	@echo "update-requirements    Create requirements.txt based on packages specified in setup.py"
	@echo "abort-if-production    Returns non-zero if in production mode (used by drop commands)"
	@echo "drop-db                Drop the database"
	@echo "drop-user              Drop the database user"
	@echo "create-user            Create the database user"
	@echo "create-db              Create the database"
	@echo "setup-db               Create the database and run all migrations"
	@echo "reset-db               Drop and recreate the database and run all migrations"
	@echo "test                   Run tests using pytest"
	@echo "help                   Print this list of targets"
