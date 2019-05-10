# In many cases it makes sense to write your own queries,
# however this provides an easy, extensible method
# of building endpoints. All that is needed
# is a table name.
# For any more specific work on the enpoint, queries
# should be written and maintained in the endpoint code
def build_sql_query(action='select', table='', fields={}, where={}, group=None, sort=None, sort_direction='DESC', limit=None, ignore=False):
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
			if isinstance(v,str) and v.startswith("RAW:"):
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
			if isinstance(v,str) and v.startswith("RAW:"):
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
						print("Comparison operator incorrectly setup, use 'value' and 'operator' fields")
				elif val is None:
					where_strs.append('%s IS NULL' % (key))
				else:
					# key = val
					where_strs.append('%s = ?' % (key,))
					params.append(val)
			query += "%s" % (' ' + where_operator + ' ').join(where_strs)
			parameters += params
	elif isinstance(where,str):
		query += " WHERE " + where

	if sort is not None:
		query += " ORDER BY `%s` %s" % (sort, sort_direction)

	if limit is not None:
		query += " LIMIT %s" % limit

	# returns query with ?'s for values and parameters
	# in order they appear in the query
	return query, parameters