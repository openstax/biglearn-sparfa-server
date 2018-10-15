from sys import version_info
from setuptools import setup, find_packages

from sparfa_server import __version__
from sparfa_server.config import PY_ENV, GITHUB_TOKEN

if version_info < (3, 5):
    raise RuntimeError('Biglearn-sparfa-server requires Python 3.5+')

if not __version__:
    raise RuntimeError('Cannot find version information')

if PY_ENV == 'travis' or PY_ENV == "production":
    BIGLEARN_SPARFA_ALGS_DEPENDENCY_LINK = (
        'git+https://{0}:x-oauth-basic@github.com/openstax/biglearn-sparfa-algs.git/'
        '@master#egg=sparfa-algs-0.0.1'.format(GITHUB_TOKEN)
    )
else:
    BIGLEARN_SPARFA_ALGS_DEPENDENCY_LINK = (
        'git+https://github.com/openstax/biglearn-sparfa-algs.git/@master#egg=sparfa-algs-0.0.1'
    )

setup(
    name='biglearn-sparfa-server',
    version=__version__,
    description='',
    long_description='',
    license='AGPLv3',
    author='OpenStax',
    author_email='',
    packages=find_packages(),
    install_requires=[
        "alembic==0.9.2",
        "amqp==2.3.2",
        "billiard==3.5.0.4",
        "celery==4.2.1",
        "celery-once==2.0.0",
        "click==6.7",
        "configobj==5.0.6",
        "dateparser==0.7.0",
        "frozendict==1.2",
        "humanize==0.5.1",
        "kombu==4.2.1",
        "mako==1.0.6",
        "markupSafe==1.0",
        "numpy==1.15.2",
        "pgcli==1.6.0",
        "pgspecial==1.8.0",
        "prompt-toolkit==1.0.14",
        "psycopg2==2.7.1",
        "pygments==2.2.0",
        "python-dateutil==2.6.0",
        "python-dotenv==0.9.1",
        "python-editor==1.0.3",
        "pytz==2017.2",
        "redis==2.10.6",
        "regex==2017.6.7",
        "requests==2.14.0",
        "ruamel.yaml==0.15.71",
        "scipy==1.1.0",
        "setproctitle==1.1.10",
        "six==1.10.0",
        "sparfa-algs==0.0.1",
        "sqlalchemy==1.2.12",
        "sqlparse==0.2.3",
        "tzlocal==1.4",
        "vine==1.1.4",
        "wcwidth==0.1.7",
    ],
    dependency_links=[BIGLEARN_SPARFA_ALGS_DEPENDENCY_LINK],
    extras_require={
        'dev': [
            'atomicwrites==1.2.1',
            'attrs==18.2.0',
            'coverage==4.5.1',
            'furl==0.5.7',
            'jsonschema==2.5.1',
            'more-itertools==4.3.0',
            'orderedmultidict==1.0',
            'pluggy==0.7.1',
            'pook==0.2.3',
            'psutil==5.4.7',
            'py==1.6.0',
            'pytest==3.8.2',
            'pytest-cov==2.5.1',
            'pytest-runner==2.11.1',
            'pytest-cov==2.5.1',
            'pyyaml==3.13',
            'multidict==4.4.2',
            'pook==0.2.3',
            'vcrpy==2.0',
            'vcrpy-unittest==0.1.7',
            'wrapt==1.10.11',
            'xmltodict==0.10.2',
            'yarl==1.2.6'
        ]
    },
    tests_require=[
        'pytest',
    ],
    setup_requires=[
        'pytest-runner'
    ],
    entry_points={
        'console_scripts': [
            'sparf=sparfa_server.cli.main:main'
        ]
    },
    classifiers=[],
)
