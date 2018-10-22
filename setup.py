from os import environ
from setuptools import setup, find_packages
from textwrap import dedent

from sparfa_server import __author__, __license__, __version__


INSTALL_REQUIRES = [
    'alembic==0.9.2',
    'amqp==2.3.2',
    'billiard==3.5.0.4',
    'celery==4.2.1',
    'celery-once==2.0.0',
    'celery-redbeat==0.11.1',
    'click==6.7',
    'dateparser==0.7.0',
    'frozendict==1.2',
    'honcho==1.0.1',
    'kombu==4.2.1',
    'Mako==1.0.6',
    'MarkupSafe==1.0',
    'numpy==1.15.2',
    'psycopg2==2.7.1',
    'python-dateutil==2.6.0',
    'python-dotenv==0.9.1',
    'python-editor==1.0.3',
    'pytz==2017.2',
    'redis==2.10.6',
    'regex==2017.6.7',
    'requests==2.14.0',
    'scipy==1.1.0',
    'six==1.10.0',
    'sparfa-algs==0.0.1',
    'SQLAlchemy==1.2.12',
    'tzlocal==1.4',
    'vine==1.1.4'
]

DEV_REQUIRE = [
    'atomicwrites==1.2.1',
    'attrs==18.2.0',
    'more-itertools==4.3.0',
    'pluggy==0.7.1',
    'py==1.6.0',
    'pycodestyle==2.4.0',
    'pytest==3.8.2'
]

TESTS_REQUIRE = DEV_REQUIRE + [
    'coverage==4.5.1',
    'pytest-cov==2.5.1',
    'pyyaml==3.13',
    'multidict==4.4.2',
    'vcrpy==2.0',
    'vcrpy-unittest==0.1.7',
    'wrapt==1.10.11',
    'yarl==1.2.6'
]
TESTS_REQUIRE.sort()

GITHUB_TOKEN = environ.get('GITHUB_TOKEN')
if GITHUB_TOKEN:
    BIGLEARN_SPARFA_ALGS_DEPENDENCY_LINK = (
        'git+https://{}:x-oauth-basic@github.com/openstax/biglearn-sparfa-algs.git/'
        '@master#egg=sparfa-algs-0.0.1'.format(GITHUB_TOKEN)
    )
else:
    BIGLEARN_SPARFA_ALGS_DEPENDENCY_LINK = (
        'git+https://github.com/openstax/biglearn-sparfa-algs.git/@master#egg=sparfa-algs-0.0.1'
    )

setup(
    name='biglearn-sparfa-server',
    version=__version__,
    author=__author__,
    url='https://github.com/openstax/biglearn-sparfa-server',
    description='Integrates SPARFA algorithms with the Biglearn servers',
    long_description=dedent("""
        Biglearn SPARFA Server integrates the SPARFA algorithms (TeSR and CLUe)
        with the Biglearn servers, allowing them to be used with OpenStax Tutor.
    """).strip(),
    license=__license__,
    packages=find_packages(),
    python_requires='>= 3.5, < 3.7',
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    extras_require={
        'dev': DEV_REQUIRE,
        'test': TESTS_REQUIRE
    },
    setup_requires=[
        'pytest-runner'
    ],
    dependency_links=[BIGLEARN_SPARFA_ALGS_DEPENDENCY_LINK],
    entry_points={
        'console_scripts': [
            'sparfa=sparfa_server.cli:main'
        ]
    }
)
