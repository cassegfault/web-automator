from scraperAPI.base import APIEndpoint

class APIError(APIEndpoint):
	type_name = "errors"

	def __init__(self):
		super(APIError,self).__init__()