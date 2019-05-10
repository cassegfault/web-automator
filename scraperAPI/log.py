from scraperAPI.base import APIEndpoint

class Log(APIEndpoint):
	type_name = "task_logs"

	def __init__(self):
		super(Log,self).__init__()