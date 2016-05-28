# pgdb - a psycopg2 DB wrapper
pgdb reads of xml config files for setting of database parameters, allowing per box configuration management of postgresql connections. 

the default config file is localhost.xml
different boxes can be configured using additional config files with them ending in the hostname (uname -n)

ie localhost.xml.myhostname, the hostname is picked up in the backround and does not need to be spefically called on wrapper initiation

there is an environment variable called DR that should point to the root directory where your python env is located

it also has prepared query mixins built in to allow for server side prepared statements, something that psycopg2 does not support natively.

also included are my modifications to the pandas iosql.sql_legacy script to allow for explicit postgresql support.  pandas has subsequently moved on to the more heavyweight use of sqlalchemy for database support.

###### usage
import pgdb
db = pgdb.database('localhost.xml')

(conn, cursor) = db.getConnCursor()

or 

conn = db.getConn()
cursor = db.getCursor()
