from task import Task
from error import APIError
from log import Log
from request import Request

from base import get_config

class ScraperAPI:
	def __init__(self):
		self.task = Task()
		self.error = APIError()
		self.log = Log()
		self.request = Request()
		self.config = get_config()

	def handle_response(self, result, task_id=None, name):
		did_error = False
		if "output" in result:
			output = result["output"]

			# This is where all results of scraping should be saved using their respective endpoints

			if "logs" in output:
				for log in result["logs"]:
					if log is None:
						continue
					if log["type"] == 'error':
						self.error.insert({ "error": "Failure during scraping script: " + log["data"] })
						did_error = True
					if log["type"] == 'navigation':
						url = log["data"]
						self.request.insert({'url':url.replace("'","''").replace('"','\"'), 'task_id':task_id, 'sent_by': name })
						if 'captcha' in url:
							self.error.insert({ 'error': "scraperAPI discovered a captcha in a request when processing the logs of task " + task_id })
							did_error = True
				self.log.insert({ 'log_json':json.dumps(result["logs"]), 'task_id':task_id })

		# This allows the autoscraper to know immediately to stop scraping
		return did_error
