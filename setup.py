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
        'alembic==0.9.2',
        'psycopg2==2.7.1',
        'requests==2.14.0',
        'SQLAlchemy==1.1.9'

    ],
    classifiers=[],
)
