import re
import sys

from setuptools import setup, find_packages

if sys.version_info < (3, 5):
    raise RuntimeError('Biglearn-sparfa-server requires Python 3.5+')

__version__ = ''
with open('sparfa_server/__about__.py', 'r') as fd:
    reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
    for line in fd:
        m = reg.match(line)
        if m:
            __version__ = m.group(1)
            break

if not __version__:
    raise RuntimeError('Cannot find version information')

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
        "click==6.7",
        "configobj==5.0.6",
        "dateparser==0.6.0",
        "frozendict==1.2",
        "humanize==0.5.1",
        "Mako==1.0.6",
        "MarkupSafe==1.0",
        "numpy==1.13.0",
        "pgcli==1.6.0",
        "pgspecial==1.8.0",
        "prompt-toolkit==1.0.14",
        "psycopg2==2.7.1",
        "Pygments==2.2.0",
        "python-dateutil==2.6.0",
        "python-editor==1.0.3",
        "pytz==2017.2",
        "regex==2017.6.7",
        "requests==2.14.0",
        "ruamel.yaml==0.15.8",
        "scipy==0.19.0",
        "setproctitle==1.1.10",
        "six==1.10.0",
        "sparfa_algs==0.0.1",
        "SQLAlchemy==1.1.9",
        "sqlparse==0.2.3",
        "tzlocal==1.4",
        "wcwidth==0.1.7",
    ],
    depencency_links=[
        'git+https://github.com/openstax/biglearn-sparfa-algs#egg=sparfa_algs'
    ],
    tests_require=[
        'pytest',
    ],
    entry_points={
        'console_scripts': [
            'sparf=sparfa_server.cli:main'
        ]
    },
    classifiers=[],
)
