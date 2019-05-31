from setuptools import setup, find_packages
from textwrap import dedent

from sparfa_server import __author__, __license__, __version__

TESTS_REQUIRE = [
    'pycodestyle',
    'pytest',
    'pytest-cov',
    'vcrpy',
    'vcrpy-unittest'
]

setup(
    name='sparfa-server',
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
    # python_requires makes the deployment fail because of https://github.com/pypa/pip/issues/5369
    # python_requires='>= 3.6',
    install_requires=[
        'alembic',
        'celery',
        'celery-once',
        'celery-redbeat',
        'click',
        'honcho',
        'kombu',
        'numpy',
        'psycopg2',
        'python-dotenv',
        'redis',
        'requests',
        'scipy',
        'sentry_sdk',
        'sparfa-algs',
        'SQLAlchemy'
    ],
    tests_require=TESTS_REQUIRE,
    extras_require={'dev': TESTS_REQUIRE},
    setup_requires=['pytest-runner'],
    entry_points={'console_scripts': ['sparfa=sparfa_server.cli:main']}
)
