[![codecov](https://codecov.io/gh/openstax/biglearn-sparfa-server/branch/master/graph/badge.svg)](https://codecov.io/gh/openstax/biglearn-sparfa-server)
[![travis](https://travis-ci.org/openstax/biglearn-sparfa-server.svg?branch=master)](https://travis-ci.org/openstax/biglearn-sparfa-server)

        ____  _       __
       / __ )(_)___ _/ /__  ____ __________
      / __  / / __ `/ / _ \/ __ `/ ___/ __ \______
     / /_/ / / /_/ / /  __/ /_/ / /  / / / /_____/
    /_______/\__, /_/\___/\__,____  /_/ /_/
      / ___//____/____ ______/ __/___ _      ________  ______   _____  _____
      \__ \/ __ \/ __ `/ ___/ /_/ __ `/_____/ ___/ _ \/ ___/ | / / _ \/ ___/
     ___/ / /_/ / /_/ / /  / __/ /_/ /_____(__  )  __/ /   | |/ /  __/ /
    /____/ .___/\__,_/_/  /_/  \__,_/     /____/\___/_/    |___/\___/_/
        /_/

## Purpose

Python tasks used to support Biglearn and conduct calculations.

## Getting Started

### Packages

Install the required dependencies:

  - Debian/Ubuntu: `sudo apt-get install libpq-dev`
  - OS X: Get [Homebrew](https://brew.sh/) if you don't already have it
          and then run `brew install postgresql`

  > NOTE: Unfortunately you need to install the postgresql package,
          because Homebrew does not currently provide a standalone libpq package.

### External Services

The following external services are required:

  - PostgreSQL 9.6
  - Redis 4.0
  - RabbitMQ 3.6

We recommend you install them using Docker and Docker Compose.
This should work on any OS that docker can be installed on:

1.  Install Docker and Docker Compose by following the instructions on the
    [Docker website](https://docs.docker.com/compose/install/)

2.  Run Docker Compose:

    `docker-compose up`

    You will now have three containers running PostgreSQL, Redis and RabbitMQ.
    `docker ps` will show the running containers.
    You can connect to the PostgreSQL database by running
    `psql postgresql://postgres@localhost:5445/postgres`.

    When you want to shut the containers down you can interrupt the `docker-compose` command.
    If you would rather run them in the background, you can run `docker-compose up -d`.

3.  If not running Docker Compose in daemon mode, open a new terminal window.

### Pyenv and pyenv-virtualenv

You will need a way to install a specific version of python,
since biglearn-sparfa-server requires python >= 3.5 and < 3.7.
We recommend `pyenv` and `pyenv-virtualenv`, and they are required to use our Makefile.
Make sure to follow all the installation instructions, including
adding the required lines to your profile and restarting the shell.

1.  Install [pyenv](https://github.com/pyenv/pyenv)

2.  Install [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv)

3.  Run `make install` to install python, create a virtualenv and install all
    dependencies using the exact versions in `requirements.txt`.

As long as it has been properly installed, pyenv-virtualenv
will automatically activate the new virtualenv for you.

If you need to update package versions, first run `make reinstall` to reset
your virtualenv to having only non-dev packages, then update the packages as needed.
When satisfied, run `make requirements` to create a new `requirements.txt`
based on the package versions currently installed in the virtualenv.
Alternatively, run `make update` to update all packages listed in `setup.py` to the
latest versions allowed, then run `make requirements` to create a new `requirements.txt`.

#### Environment Variables

1.  Run `make .env` to copy .env.example into .env

2.  Fill in the API tokens for biglearn-api and biglearn-scheduler.
    Also make sure the URLs are correct for the Biglearn servers you desire to use.

#### Database

1.  Run `make create-user setup-db` to create the
    database user and the database and run all migrations.

2.  If you need more database management commands, see `make help`.

#### Dev dependencies and tests

1.  To install the dev dependencies, run `make dev-install`.

2.  To run tests, run `make test`.

## CLI

### SPARFA Commands

  - `sparfa load` and `sparfa calc` can run individual loaders and calculations.
    Run each of these commands to obtain a list of available loaders and calculations.

  - `sparfa celery` can be used to send commands to the celery CLI, using the app's environment.
    For example: `sparfa celery worker` and `sparfa celery beat`
    Make sure you have external services running before you run this command.

### Honcho Commands

`honcho start` starts the celery worker and beat processes.
This will run all periodic tasks, including loaders and calculations.
Make sure you have the external services running before you run this command.

### Migration Commands

Alembic is used to manage migrations in biglearn-sparfa-server.

#### Running migrations

  - `alembic upgrade head` will run all migrations.

  - `alembic downgrade -1` will rollback the last migration.

  - `alembic upgrade +1` will apply the next migration.

  - `alembic history` will show the migration version history.

#### Creating migrations

Migrations are stored in the `migrations/versions` directory.
Each migration file begins with a hash and includes the
revision message that was posted at the command line.

The `sparfa_server/models.py` file contains all the models that represent
the tables in the biglearn-sparfa-server database.
The models can be changed and migration files can be autogenerated.
However, not everything can be autodetected.
Visit the
[alembic](http://alembic.zzzcomputing.com/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect)
documentation to see what can be autogenerated.

If a change has been made to the `models.py` file, run the following to create a migration file:

`alembic revision --autogenerate -m "added X column to X table"`

If a migration file needs to be created manually, instead run:

`alembic revision -m "added X table to the database"`

In either case, review the generated file in order to
add the proper migration code or make any necessary changes.
