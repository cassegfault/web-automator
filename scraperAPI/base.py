import oursql
import json
from utils import map_row

def get_config(): 
	config = {}
	with open('config.json') as config_file:
		config = json.load(config_file)
	return config

# In many cases it makes sense to write your own queries,
# however this provides an easy, extensible method
# of building endpoints. All that is needed
# is a table name.
# For any more specific work on the enpoint, queries
# should be written and maintained in the endpoint code
def build_query(action='select', table='', fields={}, where={}, group=None, sort=None, sort_direction='DESC', limit=None, ignore=False):
	parameters = []
	query = ""
	
	if action.lower() == 'insert':
		query = "INSERT "
		if ignore:
			query += "IGNORE "
		query += "INTO `%s` " % table
		# https://docs.python.org/2/library/stdtypes.html#dict.items
		# These will correspond
		query += "(%s)" % ','.join(['`%s`' % field for field in fields.keys()])
		vals = []
		for v in fields.values():
			if isinstance(v,basestring) and v.startswith("RAW:"):
				vals.append(v.replace("RAW:",''))
			else:
				vals.append('?')
		query += " VALUES (%s)" % ','.join([str(v) for v in vals])
		parameters += fields.values()

	elif action.lower() == 'update':
		query = "UPDATE "
		if ignore:
			query += "IGNORE "
		query += "`%s` " % table
		query += " SET "
		vals = []
		for k,v in fields.iteritems():
			if isinstance(v,basestring) and v.startswith("RAW:"):
				vals.append('`%s`=%s' % (k, v.replace("RAW:",'')))
			else:
				vals.append('`%s`=?' % (k,))
				parameters.append(v)
		query += "%s" % ', '.join([str(piece) for piece in vals])

	elif action.lower() == 'select':
		if isinstance(fields, dict):
			fields = fields.keys()
		query = "SELECT "
		query += ','.join(['`%s`' % str(field) for field in fields])
		query += " FROM `%s` " % table

	if isinstance(where,dict):
		if len(where.keys()) > 0:
			query += " WHERE "
			where_strs = []
			where_operator = "AND"
			params = []
			for key,val in where.iteritems():
				if key == 'where_op':
					where_operator = val
					continue
				if isinstance(val,list):
					where_strs.append('%s IN (%s)' % (key,','.join([str(i) for i in val])))
				elif isinstance(val,dict):
					# this is a method for comparison operators
					try:
						where_val = val['val']
						# raw values for INTERVAl 7 DAY or similar,
						# otherwise escape and quote strings
						raw_value = 'raw' in val[:3]
						if raw_value:
							where_strs.append('`%s` %s %s' % (key,val['operator'],where_val))
						else:
							where_strs.append('`%s` %s ?') % (key, val['operator'])
							params.append(where_val)
					except:
						print "Comparison operator incorrectly setup, use 'value' and 'operator' fields"
				elif val is None:
					where_strs.append('%s IS NULL' % (key))
				else:
					# key = val
					where_strs.append('%s = ?' % (key,))
					params.append(val)
			query += "%s" % (' ' + where_operator + ' ').join(where_strs)
			parameters += params
	elif isinstance(where,basestring):
		query += " WHERE " + where

	if sort is not None:
		query += " ORDER BY `%s` %s" % (sort, sort_direction)

	if limit is not None:
		query += " LIMIT %s" % limit

	# returns query ready for opensql with ?'s for values
	# and parameters in order they appear in the query
	return query, parameters

# Singleton DB connection so I don't leave a million open
class APIDBConnection:
	instance = None
	def __init__(self):
		if not APIDBConnection.instance:
			config = get_config()
			APIDBConnection.instance = self.connection = oursql.connect(host=config['db_host'], user=config['db_user'], passwd=config['db_password'], db=config['database'], autoping=True, raise_on_warnings=False)
	def __getattr__(self, name):
		return getattr(self.instance, name)


# Gives every type a DB connection and basic functionality
class APIEndpoint(object):
	default_limit = 250
	type_name=''
	
	def __init__(self):
		self.conn = APIDBConnection()
		self.c = self.conn.cursor()
		
		self.type_description = {}
		self.c.execute("DESCRIBE %s" % self.type_name)
		for row in self.c.fetchall():
			self.type_description[row[0]] = row[1]

	def limit_fields(self, fields):
		if isinstance(fields, dict):
			final_fields = {}
			for field in fields.keys():
				if field in self.type_description.keys():
					final_fields[field] = fields[field]
			return final_fields
		elif isinstance(fields, list):
			final_fields = []
			for field in fields:
				if field in self.type_description.keys():
					final_fields.append(field)
			return final_fields
		return None

	def get_all(self, limit=None, sort=None, sort_direction='DESC'):
		all_results = []
		limit = limit or self.default_limit
		query, params = build_query(action='select', table=self.type_name, fields=self.type_description, limit=limit, sort=sort, sort_direction=sort_direction)
		self.c.execute(query, params)
		
		query_description = self.c.description

		for raw in self.c.fetchall():
			row = map_row(query_description, raw)
			all_results.append(row)

		return all_results

	def get_by_fields(self, fields=None, field='', value='', sort=None, sort_direction='DESC'):
		where_dict = {}
		if fields is None:
			where_dict[field] = value
		else:
			where_dict = fields
		query, params = build_query(action='select', table=self.type_name, fields=self.type_description, where=where_dict, sort=sort, sort_direction=sort_direction)
		self.c.execute(query, params)
		
		query_description = self.c.description

		all_results = []
		for raw in self.c.fetchall():
			row = map_row(query_description, raw)
			all_results.append(row)

		return all_results

	def update_or_insert(self, fields, where_key="id", allow_nulls=True):
		existing_items = []

		fields = self.limit_fields(fields)

		if not allow_nulls:
			to_loop = fields.keys()
			for field in to_loop:
				if fields[field] is None:
					del fields[field]

		if where_key in fields:
			existing_items = self.get_by_fields(field=where_key, value=fields[where_key])

		if len(existing_items) > 0:
			self.update_by_fields(fields, where_key=where_key)
		else:
			query, params = build_query(action='insert', table=self.type_name, fields=fields)
			self.c.execute(query,params)
			self.conn.commit()
		return self.c.lastrowid

	def update_by_fields(self, item, fields=None, where_key='id'):	
		fields = self.limit_fields(fields)

		if fields is None and where_key is not None and where_key in item:
			fields = {}
			fields[where_key] = item[where_key]

		query, params = build_query(action='update', table=self.type_name, fields=item, where=fields)
		self.c.execute(query,params)
		self.conn.commit()
		return self.c.lastrowid
	
	def insert(self, item, ignore=False):
		item = self.limit_fields(item)
		query, params = build_query(action='insert', table=self.type_name, fields=item, ignore=ignore)
		self.c.execute(query,params)
		self.conn.commit()
		return self.c.lastrowid

	def insert_many(self, items):
		return_ids = []
		for item in items:
			item = self.limit_fields(item)
			query, params = build_query(action='insert', table=self.type_name, fields=item)
			self.c.execute(query,params)
			return_ids.append(self.c.lastrowid)
		self.conn.commit()
		return return_ids
