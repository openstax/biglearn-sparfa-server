.PHONY: dotenv python uninstall-python virtualenv venv uninstall-virtualenv uninstall-venv \
	      reset-virtualenv reset-venv install install-dev reinstall reinstall-dev update \
				requirements freeze abort-if-production create-user drop-user create-db setup-db drop-db \
				reset-db serve server test clean-build clean-pyc clean-test clean help
.DEFAULT_GOAL := help

PYTHON_VERSION := 3.6.6
VIRTUALENV_NAME := biglearn-sparfa-server

.python.env:
	cp .python.env.example .python.env

dotenv: .python.env

python:
	pyenv install --skip-existing ${PYTHON_VERSION}

uninstall-python:
	pyenv uninstall --force ${PYTHON_VERSION}

virtualenv: python
	pyenv virtualenv --force ${PYTHON_VERSION} ${VIRTUALENV_NAME}
	pyenv local ${VIRTUALENV_NAME}
	pip install --upgrade pip

venv: virtualenv

.python-version:
	make virtualenv

uninstall-virtualenv:
	pyenv uninstall --force ${VIRTUALENV_NAME}
	rm -f .python-version

uninstall-venv: uninstall-virtualenv

reset-virtualenv: uninstall-virtualenv virtualenv

reset-venv: reset-virtualenv

install: .python-version
	pip install -r requirements.txt

install-dev: .python-version install
	pip install -e .[dev]

reinstall: reset-virtualenv install

reinstall-dev: reset-virtualenv install-dev

update: reset-virtualenv
	pip install --no-deps -e git+git@github.com:openstax/biglearn-sparfa-algs#egg=sparfa_algs
	pip install -e .

requirements: .python-version
	if [ -z "$$(pip freeze)" ]; then make install; fi
	echo "$$(pip freeze)" | \
	sed -Ee 's/-e git\+(https:\/\/|git@)github\.com(\/|:)openstax\/biglearn-sparfa-server\.git@[0-9a-f]+#egg=sparfa_server/-e ./' > requirements.txt

freeze: requirements

abort-if-production: .python.env
	if [ -z "$${PY_ENV}" ]; then . ./.python.env; fi && [ "$${PY_ENV}" != "production" ]

create-user: .python.env
	. ./.python.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "CREATE USER $${PG_USER} WITH SUPERUSER PASSWORD '$${PG_PASSWORD}'"

drop-user: .python.env abort-if-production
	. ./.python.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "DROP USER IF EXISTS $${PG_USER}"

create-db: .python.env
	. ./.python.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U postgres \
	                 -c "CREATE DATABASE $${PG_DB} ENCODING 'UTF8'"

setup-db: .python-version create-db
	alembic upgrade head

drop-db: .python.env abort-if-production
	. ./.python.env && psql -h $${PG_HOST} -p $${PG_PORT} -d postgres -U $${PG_USER} \
	                 -c "DROP DATABASE IF EXISTS $${PG_DB}"

reset-db: drop-db setup-db

serve: .python.env .python-version
	gunicorn --reload --worker-class gevent sparfa_server.flask

server: serve

test: .python.env install-dev
	pytest
	pycodestyle

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

help:
	@echo "The following targets are available:"
	@echo
	@echo ".python.env/dotenv     Copy .python.env.example into .python.env"
	@echo "python                 Install Python ${PYTHON_VERSION} using pyenv"
	@echo "uninstall-python       Uninstall Python ${PYTHON_VERSION} using pyenv"
	@echo "v[irtual]env           Create ${VIRTUALENV_NAME} using pyenv-virtualenv"
	@echo "uninstall-v[irtual]env Uninstall ${VIRTUALENV_NAME} using pyenv-virtualenv"
	@echo "install                Install pip packages using versions in requirements.txt"
	@echo "install-dev            Install dev pip packages listed in setup.py"
	@echo ".python-version        Create the virtualenv if .python-version does not exist"
	@echo "reset-v[irtual]env     Run make uninstall-virtualenv, then make virtualenv"
	@echo "reinstall              Run make reset-virtualenv, then make install"
	@echo "reinstall-dev          Run make reset-virtualenv, then make install-dev"
	@echo "update                 Update all pip packages to the latest available versions"
	@echo "requirements/freeze    Recreate requirements.txt based on installed packages"
	@echo "abort-if-production    Returns non-zero if in production mode"
	@echo "create-user            Create the database user"
	@echo "drop-user              Drop the database user"
	@echo "create-db              Create the database"
	@echo "setup-db               Create the database and run all migrations"
	@echo "drop-db                Drop the database"
	@echo "reset-db               Drop and recreate the database and run all migrations"
	@echo "serve[r]               Run gunicorn in development mode"
	@echo "test                   Run tests using pytest"
	@echo "clean-build            Remove build artifacts"
	@echo "clean-pycache          Remove pycache artifacts"
	@echo "clean-test             Remove test artifacts"
	@echo "clean                  Remove build, pycache, and test artifacts"
	@echo "help                   Print this list of targets"
