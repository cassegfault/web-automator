from scraperAPI.base import build_query, APIEndpoint

class Request(APIEndpoint):
	type_name = "requests"

	def __init__(self):
		super(Request,self).__init__()

	def get_last_days_requests(self, days=1, sent_by=None):
		if sent_by is None:
			self.c.execute("SELECT count(*) FROM requests WHERE date_added > DATE_SUB(NOW(), INTERVAL %d DAY)" % int(days))
		else:
			self.c.execute("SELECT count(*) FROM requests WHERE sent_by=? AND date_added > DATE_SUB(NOW(), INTERVAL %d DAY)" % int(days), sent_by)
		return self.c.fetchall()[0][0]