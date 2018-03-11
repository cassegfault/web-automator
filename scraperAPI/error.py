from base import build_query, APIEndpoint

class APIError(APIEndpoint):
	type_name = "errors"

	def __init__(self):
		super(APIError,self).__init__()