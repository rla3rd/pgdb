from setuptools import setup
from pgdb import __version__

setup(
    name='pgdb',
    description='pgdb database connector',
    author='Richard Albright',
    version=__version__,
    requires=['psycopg2', 'sqlalchemy'],
    py_modules=['pgdb'],
    license='MIT License')
