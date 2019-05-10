from abc import ABC, abstractmethod

# Defines a parent class for DB Adapters to inherit from
# Adapters will not be able to be instantiated until all
# abstract members are implemented in the child
class DBAdapter(ABC):
	__connection = None
	@abstractmethod
	def __constructor__(self, config):
		pass
	
	@abstractmethod
	def cursor(self):
		pass

	@abstractmethod
	def commit(self):
		pass
	
	@abstractmethod
	def rollback(self):
		pass
	
	@abstractmethod
	def ping(self):
		pass
	
	@abstractmethod
	def close(self):
		pass
	
	def raw_connection(self):
		return self.__connection

# Defines a cursor wrapper for each DB implementation
class DBAdapterCursor(ABC):
	__cursor = None
	# Must implement a constructor which instantiates the raw cursor
	@abstractmethod
	def __constructor__(self, connection):
		pass
	
	# execute some query with an undefined number of arguments
	@abstractmethod
	def execute(self, query, *args):
		pass
	
	# execute the same query over a list of argument sets
	@abstractmethod
	def executeMany(self, query, data):
		pass
	
	# build a query based on keyword parameters to minimize the amount of
	# SQL (or other query language) needed to be written by the end user
	@abstractmethod
	def buildAndExecute(self, action, table, fields, where, group, sort, sort_direction, limit, ignore):
		pass
	
	# return a single row from the result set
	@abstractmethod
	def fetchone(self):
		pass
	
	# return all rows from the result set
	@abstractmethod
	def fetchall(self):
		pass
	
	# close the cursor
	@abstractmethod
	def close(self):
		pass
	
	# return the description of the table
	@abstractmethod
	def describe(self):
		pass
	
	# return the last update or insert row ID
	@abstractmethod
	def lastrowid(self):
		pass

	# return the number of rows in the result set
	@abstractmethod
	def rowcount(self):
		pass

	# return the raw cursor
	def raw_cursor(self):
		return self.__cursor