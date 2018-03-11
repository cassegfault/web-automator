import re

def map_row(description, row):
	if row is None:
		return None
	return_row = {}
	for idx, item in enumerate(description):
		if item is None:
			continue
		name = item[0]
		return_row[name] = row[idx]
	return return_row