from scraperAPI.base import APIEndpoint

class Task(APIEndpoint):
	type_name = "tasks"

	def __init__(self):
		super(Task,self).__init__()

	def mark_complete(self, task):
		data = {
			'date_completed': 'RAW:CURRENT_TIMESTAMP',
		}
		
		if task['schedule_type'] != 'once':
			data['date_next_run'] = 'RAW:DATE_ADD(NOW(), INTERVAL %s %s)' % (task['interval'], task['schedule_type'])
			self.c.execute("""UPDATE tasks SET 
											date_completed=CURRENT_TIMESTAMP,
											date_next_run=DATE_ADD(NOW(), INTERVAL ? ?) 
											WHERE id=?""", (task['interval'], task['schedule_type'], task['id']) )
		else:
			self.c.execute("UPDATE tasks SET date_completed=CURRENT_TIMESTAMP WHERE id=?",(task['id'],))

		
		self.conn.commit()
		return self.c.lastrowid

	def get_current_tasks(self):
		where = "(date_next_run IS NULL OR date_next_run < NOW()) AND currently_running=0"
		return self.get_by_fields(fields=where, sort='priority', sort_direction='ASC')