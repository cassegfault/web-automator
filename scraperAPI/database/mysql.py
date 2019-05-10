from scraperAPI.database import DBAdapterCursor, DBAdapter
from scraperAPI.database.SQLBuildQuery import build_sql_query
import mysql.connector
class MySQLDBCursor(DBAdapterCursor):
	__cursor = None
	def __constructor__(self, connection):
		self.__cursor = connection.raw_connection.cursor()
	
	def __convert_query_params(self,query):
		return query.replace('?','%s')

	def execute(self, query, args):
		query = self.__convert_query_params(query)
		return self.__cursor.execute(query, args)

	def executeMany(self, query, data):
		query = self.__convert_query_params(query)
		return self.__cursor.executeMany(query, data)
	
	def buildAndExecute(self, **kwargs):
		query, params = build_sql_query(*kwargs)
		query = self.__convert_query_params(query)
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
		self.execute("DESCRIBE ?", table_name)
		type_description = {}
		for row in self.fetchall():
			type_description[row[0]] = row[1]
		return type_description
	
	def lastrowid(self):
		return self.__cursor.lastrowid
	
	def rowcount(self):
		return self.__cursor.rowcount

	

class MySQLDB(DBAdapter):
	__connection = None
	def __constructor__(self, config):
		self.__connection = mysql.connector.connect(host=config['db_host'], user=config['db_user'], password=config['db_password'], database=config['database'], autoping=True, raise_on_warnings=False)

	def cursor(self):
		return MySQLDBCursor(self.__connection)
	
	def commit(self):
		return self.__connection.commit()
	
	def rollback(self):
		return self.__connection.rollback()
	
	def ping(self):
		return self.__connection.ping()
	
	def close(self):
		return self.__connection.close()