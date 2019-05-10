from abc import ABC, abstractmethod

class DBImplementation(ABC):
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
	def raw_connection(self):
		pass

class DBCursorImplementation(ABC):
	__cursor = None
	@abstractmethod
	def __constructor__(self):
		pass
	
	@abstractmethod
	def execute(self, query):
		pass
	
	@abstractmethod
	def executeMany(self, query):
		pass
	
	@abstractmethod
	def fetchone(self):
		pass
	
	@abstractmethod
	def fetchall(self):
		pass
	
	@abstractmethod
	def close(self):
		pass
	
	@abstractmethod
	def definition(self):
		pass
	
	@abstractmethod
	def lastrowid(self):
		pass

	@abstractmethod
	def rowcount(self):
		pass

	@abstractmethod
	def raw_cursor(self):
		pass