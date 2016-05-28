import re
import os
import uuid
import inspect
from xml.etree import ElementTree as etree
import psycopg2
from  psycopg2.extras import RealDictCursor
from psycopg2.extensions import connection
from psycopg2.extensions import adapt

__version__ = '1.1.1'

env = os.environ
home = env["DR"]

pyPath = "%s/python" % home

class database( object ):

    def __repr__( self ):
        return "Host: %s, Port: %s, Database: %s, User: %s, Password: %s Application_name %s" % \
             ( self.host, self.port, self.database, self.user, self.password, self.appname )

    def __init__( self, configFile, mode='ro' ):

        self.formatRe = re.compile('(\%s|\%\([\w\.]+\)s)', re.DOTALL)
        self.prepCache = {}
   
        os.chdir( pyPath )

        boxName =os.uname()[1]

        if os.path.exists( '%s.%s' % ( configFile, boxName ) ):
            configFile = '%s.%s' % ( configFile, boxName ) 
        xmlfile = open('%s/%s' % ( pyPath, configFile ))
        tree = etree.parse(xmlfile)
        option = tree.getroot()
        
        self.host = option.find('host').text
        self.port = int( option.find('port').text )
        self.database = option.find('database').text
        self.user = option.find('user').text
        self.password = option.find('password').text
	self.appname = "%s.%s.%s" % (boxName, os.getpid(), inspest.stack()[-1][1])
        if mode == 'ro' or mode == 'RO':
            self.readonly = True
        elif mode == 'rw' or mode =='RW':
            self.readonly = False
        else:
            self.readonly = True
        self.adapt = adapt
        xmlfile.close()

        self.conn = connection( "host = %s port = %s dbname = %s user = %s password = %s application_name = %s" % \
            ( self.host, self.port, self.database, self.user, self.password, self.appname ) )

        if psycopg2.__version__.split(' ')[0] >= '2.4.2':
            self.conn.set_session(readonly=self.readonly, autocommit=True)
        
        self.cursor = self.conn.cursor( cursor_factory = RealDictCursor )

    def prepare(self, cmd):
        '''
        translate a sql command into its corresponding 
        prepared statement, and execute the declaration.
        '''
        specifiers = []

        def replaceSpec(mo):
            specifiers.append(mo.group())
            return '$%d' % len(specifiers)

        replacedCmd = self.formatRe.sub(replaceSpec, cmd)
        cmdId = 'prepared%s' % str(uuid.uuid1()).replace('-','')

        prepCmd = 'prepare %s as %s' % (cmdId, replacedCmd)

        if len(specifiers) == 0:    # no variable arguments
            execCmd = 'execute %s' % cmdId

        else:       # set up argument slots in prep statement
            execCmd = 'execute %s(%s)' % (cmdId, ', '.join(specifiers))

        self.cursor.execute(prepCmd)
        self.prepCache[execCmd] = execCmd
        return execCmd

    def execPrepared(self, cmd, args=None):
        '''
        execute a command using a prepared statement.
        '''
        prepStmt = self.prepCache.get(cmd)
        if prepStmt is None:
            cmdId = 'prepared%s' % str(uuid.uuid1()).replace('-','')
            # unique name for new prepared statement
            prepStmt = self.prepCache[cmd] = \
                       self.prepare(cmd, cmdId)

        self.cursor.execute(prepStmt, args)

    def getConnCursor( self ):
        return ( self.conn, self.cursor )

    def getConn( self ):
	return self.conn

    def getCursor( self )
	return self.cursor
