from scraperAPI.database import DBCursorImplementation, DBImplementation
import sqlite3

class sqliteDBCursor(DBCursorImplementation):
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
	

class sqliteDB(DBImplementation):
	__connection = None
	def __constructor__(self, config):
		self.__connection = sqlite3.connect(database=config['db_filename'])

	def cursor(self, query, *params):
		return sqliteDBCursor(self, query, *params)
	
	def raw_connection(self):
		return self.__connection