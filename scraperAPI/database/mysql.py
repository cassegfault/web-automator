from scraperAPI.database import DBCursorImplementation, DBImplementation
import mysql.connector
class MySQLDBCursor(DBCursorImplementation):
	__cursor = None
	def __constructor__(self, connection):
		self.__cursor = connection.raw_connection.cursor()

	def execute(self, query, *args):
		return self.__cursor.execute(query, *args)

	def executeMany(self, operation, data):
		return self.__cursor.executeMany(operation, data)
	
	def fetchone(self):
		return self.__cursor.fetchone()

	def fetchall(self):
		return self.__cursor.fetchall()
	
	def close(self):
		return self.__cursor.close()

	def definition(self):
		return self.__cursor.definition
	
	def lastrowid(self):
		return self.__cursor.lastrowid
	
	def rowcount(self):
		return self.__cursor.rowcount

	def raw_cursor(self):
		return self.__cursor
	

class MySQLDB(DBImplementation):
	__connection = None
	def __constructor__(self, config):
		self.__connection = mysql.connector.connect(host=config['db_host'], user=config['db_user'], password=config['db_password'], database=config['database'], autoping=True, raise_on_warnings=False)

	def cursor(self, query, *params):
		return MySQLDBCursor(self, query, *params)
	
	def raw_connection(self):
		return self.__connection