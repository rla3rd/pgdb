import re
import os
import inspect
import socket
import json
import psycopg2
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from psycopg2.extras import DictCursor
from psycopg2.extensions import adapt
import sys
import traceback

__version__ = '2.0.0'

env = os.environ
home = os.path.expanduser("~")
cfgPath = env.get("PGDB_HOME", home)


def errorDetails():
    error = sys.exc_info()[0]
    details = traceback.format_exc()
    sys.stderr.write(f"{error}, {details}")


class PrepareCursor(object):
    '''
    mix in with dbapi cursor class

    formatRe fishes out all format specifiers for a given paramstyle
    this one works with paramstyles 'qmark', 'format' or 'pyformat'
    '''
    formatRe = re.compile('(\%s|\%\([\w\.]+\)s)', re.DOTALL)

    def __init__(self, *a, **kw):
        super(PrepareCursor, self).__init__(*a, **kw)

        self.prepCache = {}

    def execPrepared(self, cmd, args=None):
        '''
        execute a command using a prepared statement.
        '''
        prepStmt = self.prepCache.get(cmd)
        if prepStmt is None:
            cmdId = f"ps_{len(self.prepCache) + 1}"
            # unique name for new prepared statement
            prepStmt = self.prepCache[cmd] = \
                self.prepare(cmd, cmdId)

        self.execute(prepStmt, args)

    def prepare(self, cmd, cmdId):
        '''
        translate a sql command into its corresponding
        prepared statement, and execute the declaration.
        '''
        specifiers = []

        def replaceSpec(mo):
            specifiers.append(mo.group())
            return f"${len(specifiers)}"

        replacedCmd = self.formatRe.sub(replaceSpec, cmd)
        prepCmd = f"prepare {cmdId} as {replacedCmd}"

        if len(specifiers) == 0:    # no variable arguments
            execCmd = f"execute {cmdId}"

        else:       # set up argument slots in prep statement
            execCmd = f"execute {cmdId}({', '.join(specifiers)})"

        self.execute(prepCmd)
        self.prepCache[execCmd] = execCmd

        return execCmd

    def execManyPrepared(self, cmd, seq_of_parameters):
        '''
        prepared statement version of executemany.
        '''
        for p in seq_of_parameters:
            self.execPrepared(cmd, p)

        # Don't want to leave the value of the last execute() call
        try:
            self.rowcount = -1
        except TypeError:   # fooks with psycopg
            pass


class Cursor(PrepareCursor, DictCursor):
    pass


class database(object):

    def __repr__(self):
        return " ".join([
            f"Host: {self.host}",
            f"Port: {self.port}",
            f"Database: {self.database}",
            f"User: {self.user}",
            f"Password: {self.password}",
            f"Application_name: {self.appname}"])

    def __init__(self, mode='rw', pool_size=1, configFile='pgdb.json'):

        boxName = os.uname()[1]

        if os.path.exists(f"{cfgPath}/{configFile}.{boxName}"):
            configFile = f"{configFile}.{boxName}"

        print(f"{cfgPath}/{configFile}")
        file = open(f"{cfgPath}/{configFile}", "rb")
        option = json.loads(file.read())
        file.close()
        self.host = option.get('host')
        self.port = option.get('port')
        self.database = option.get('database')
        self.user = option.get('user')
        self.password = option.get('password')
        skt = socket.gethostname()
        pid = os.getpid()
        id = os.environ.get('UNIQUE_ID', '')
        bsname = os.path.basename(inspect.stack()[-1][1])
        self.appname = f"{skt}.{pid}.{id}.{bsname}"
        if mode == 'ro' or mode == 'RO':
            self.readonly = True
        else:
            self.readonly = False
        self.adapt = adapt

        try:
            connString = "".join([
                f"postgresql://{self.user}",
                f":{self.password}@",
                f"{self.host}:",
                f"{self.port}/",
                f"{self.database}?",
                f"application_name={self.appname}"])
            db = create_engine(
                connString,
                poolclass=NullPool,
                connect_args={'connect_timeout': 10})
            self.engine = db.engine
            self.conn = db.engine.raw_connection()
            # the connection starts in transaction mode
            # that needs rolled back in order
            # to set the session in autocommit mode
            self.conn.rollback()
            self.conn.set_session(readonly=self.readonly, autocommit=True)
            self.cursor = self.conn.cursor(cursor_factory=Cursor)
            self.available = True
            self.cursor.execute("set statement_timeout='10min'")

        except sqlalchemy.exc.OperationalError:
            self.available = False
            self.conn = None
            self.cursor = None
            self.engine = None

    def autocommit(self, auto):
        if auto is False:
            self.conn.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED)
        if auto is True:
            self.conn.set_isolation_level(
                psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    def getEngineConnCursor(self):
        return (self.engine, self.conn, self.cursor)

    def getConnCursor(self):
        return (self.conn, self.cursor)

    def getConn(self):
        return self.conn

    def getCursor(self):
        return self.cursor

    def getEngine(self):
        return self.engine
