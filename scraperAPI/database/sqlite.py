from scraperAPI.database import DBAdapterCursor, DBAdapter
from scraperAPI.database.SQLBuildQuery import build_sql_query
import sqlite3

class sqliteDBCursor(DBAdapterCursor):
	__cursor = None
	def __constructor__(self, connection):
		self.__cursor = connection.raw_connection.cursor()

	def execute(self, query, args):
		return self.__cursor.execute(query, args)

	def executeMany(self, operation, data):
		return self.__cursor.executeMany(operation, data)
	
	def buildAndExecute(self, **kwargs):
		query, params = build_sql_query(*kwargs)
		return self.__cursor.execute(query,params)
	
	def fetchone(self):
		return self.__cursor.fetchone()

	def fetchall(self):
		return self.__cursor.fetchall()
	
	def close(self):
		return self.__cursor.close()

	def description(self):
		return self.__cursor.description

	def table_definition(self, table_name):
		self.execute("PRAGMA table_info(?)",table_name)
		type_description = {}
		for row in self.fetchall():
			type_description[row[1]] = row[2]
		return type_description
	
	def lastrowid(self):
		return self.__cursor.lastrowid
	
	def rowcount(self):
		return self.__cursor.rowcount
	

class sqliteDB(DBAdapter):
	__connection = None
	def __constructor__(self, config):
		self.__connection = sqlite3.connect(database=config['db_filename'])

	def cursor(self):
		return sqliteDBCursor(self.__connection)
	
	def commit(self):
		return self.__connection.commit()
	
	def rollback(self):
		return self.__connection.rollback()
	
	def ping(self):
		# because sqlite is file based, ping isn't a thing
		pass
	
	def close(self):
		return self.__connection.close()