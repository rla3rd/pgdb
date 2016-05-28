from setuptools import setup
from pgdb import __version__
 
setup( name='pgdb',
    description='Postgres Database Connector',
    author='Richard Albright',
    version=__version__,
    requires=['psycopg2', 're', 'os', 'xml'],
    py_modules=['pgdb', 'sql_legacy'],
    license='MIT License' )
