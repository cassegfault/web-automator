from scraperAPI import ScraperAPI
from utils import debug_log, force_utf8
from datetime import datetime
import time
import json
import subprocess
import oursql

from email.mime.text import MIMEText
import smtplib

class Automator():
	def __init__(self, config_filename):
		self.is_running = False
		self.did_error = False
		self.load_config(config_filename)
		self.api = ScraperAPI()
		self.conn = oursql.connect(host=self.config['db_host'], user=self.config['db_user'], passwd=self.config['db_password'], db=self.config['database'], raise_on_warnings=False)
		self.c = self.conn.cursor()

	def load_config(self,config_filename):
		self.config = {}
		with open(config_filename) as config_file:
			self.config = json.load(config_file)

	def debug_log(*args):
		if 'debug' in self.config and self.config['debug']:
			print args

	def error_check(self):
		self.c.execute("SELECT count(*), returned_error FROM requests WHERE `sent_by`='%s' AND date_added > DATE_SUB(NOW(), INTERVAL 7 DAY)" % config['name'])
		w_rows = self.c.fetchall()
		week_requests = w_rows[0][0]
		self.did_error = (w_rows[0][1] > 0)

		weekly_allotment = config["weekly_request_limit"]

		self.c.execute("SELECT count(*) FROM requests WHERE `sent_by`='%s' AND  date_added > DATE_SUB(NOW(), INTERVAL 18 HOUR)" % config['name'])
		t_rows = self.c.fetchall()
		today_requests = t_rows[0][0]

		# If any job has errored, hold off for a while
		self.c.execute("SELECT count(id) FROM errors WHERE job_id IS NOT NULL AND is_resolved=0 ")
		err_rows = self.c.fetchall()
		if err_rows is not None and err_rows[0] is not None and err_rows[0][0] > 0:
			self.did_error = True

		if week_requests > weekly_allotment or today_requests > (weekly_allotment / 7) or self.did_error:
			# we're out of requests for the week, we can start sleeping longer
			debug_log( "Stopping requests for the week due to an error or number of requests", self.did_error, today_requests, weekly_allotment )
			if self.did_error:
				update_server_status('Sleeping due to an error')
			else:
				update_server_status('Sleeping due to requests')
			self.did_error = True

	def raise_error(self, error, save_error=True):
		if isinstance(error, basestring):
			error = { 'error': error }
		
		if save_error:
			try:
				self.api.error.insert(error)
			except UnicodeDecodeError:
				self.api.error.insert({ 'error': 'Could not write error, check logs' })
		self.did_error = True

		# Send an email notification
		msg = MIMEText("Autoscraper encountered an error and is no longer running\n\n"+json.dumps(error))
		msg['Subject'] = "Error from Autoscraper"
		msg['From'] = '"Autoscraper" <noreply@example.domain>'
		msg['Sender'] = 'noreply@example.domain'
		msg['To'] = "chris@v3x.pw"
		s = smtplib.SMTP('localhost')
		s.sendmail('noreply@example.domain',['chris@v3x.pw'], msg.as_string())

	def build_queue(self):
		# Grab all the jobs from the DB, order properly
		all_jobs = self.api.task.get_current_tasks()

		script_jobs = defaultdict(lambda: [])
		for job in all_jobs:
			additional_parameters = json.loads(job['additional_parameters'])
			# Make sure the right bots run the right jobs
			if 'only_bot' in additional_parameters:
				if 'name' in config and additional_parameters['only_bot'] != config['name']:
					continue
			elif 'only_directed_jobs' in config and config['only_directed_jobs']:
				continue

			if 'accept_tasks' in config:
				if job['script'] not in config['accept_tasks']:
					continue

			if job['schedule_type'] == 'once' and job['date_completed'] is not None:
				continue
			# only make actually available jobs available
			script_jobs[job['script']].append(job)

		self.job_list = []
		self.available_job_types = script_jobs.keys()
		
		dont_run_script = None
		if len(self.last_run_types) > 0:
			last_run_script = self.last_run_types[0]
			# count how many of this job we've done
			count = 0
			for t in self.last_run_types:
				if t == last_run_script:
					count += 1
				else:
					break

			# Dont run it if we've done it too many times
			if count > 5:
				dont_run_script = None

		# This is a good place for finer grain prioritization

	def handle_response(self, result={}):
		debug_log("Handling Response")
		did_error = False
		if "output" in result:
			did_error = self.api.handle_response(result, task_id=self.current_job["id"], name=self.config['name'])

		if "error" in result:
			self.raise_error(json.dumps(result["error"]))
			debug_log("response contained error")

		if did_error:
			self.raise_error("Error encountered in logs", save_error=False)

	def run_job(self,job):
		self.api.task.update_by_fields(item={ 'id':job['id'], 'date_started':'RAW:CURRENT_TIMESTAMP' })
		
		self.current_job = job
		script = job['script']

		# This may seem frivolous but it provides a layer of protection against fucked up tasks
		# and allows us to not even spin up v8 if it's not necessary
		additional_parameters = json.loads(job["additional_parameters"])
		if 'only_bot' in additional_parameters:
			if 'name' in self.config and additional_parameters['only_bot'] != self.config['name']:
				self.raise_error({ 'task_id':job['id'], 'error': 'Could not parse JSON in job parameters' })
				return None

		process = subprocess.Popen([ self.config['node_location'],
									'scraper/scripts/' + script + '.js', 
									job["additional_parameters"],
									config['filename'] ], 
									stdout=subprocess.PIPE)

		# The subprocess only sends one line.
		# Append all the data and break on a code being returned
		lines = []
		return_code = None
		while self.is_running:
			line = process.stdout.readline()
			if line != '':
				lines.append(line)
			
			return_code = process.poll()
			if return_code is not None:
				break

		# If scripts are written poorly they send multiple lines
		# The last line will always be the full output
		final_line = lines.pop()

		# if the subprocess errors, we need to error
		if return_code != 0:
			self.raise_error({ 'task_id':job['id'], 'error': 'Subprocess exited with error code: ' + str(return_code) })
			return

		full_response = {}
		try:
			full_response = json.loads(final_line)
		except:
			self.raise_error({ 'task_id':job['id'], 'error':'JSON could not parse returned results: ' + final_line })

		did_error = False
		try:
			did_error = self.handle_response(full_response)
		except oursql.ProgrammingError as strerr:
			self.raise_error({ 'task_id':job['id'], 'error':'Error handling result from JSON: ' + str(force_utf8(strerr)) + ' \n\n' + full_line })

		if did_error:
			self.raise_error("Encountered an error while handling results", save_error=False)

		self.api.task.mark_complete(job)

	def is_business_hours(self):
		now_time = datetime.now()
		dow = now_time.weekday()
		hour = now_time.hour

		if dow >= 0 and dow <= 5:
			hours = self.config["hours"]
			for shift in hours:
				# if we are in a valid shift, return
				if hour >= shift["start"] and hour < shift["end"]:
					return True

		# if none of the shifts returned, we are not running
		return False

	def quit(self):
		self.is_running = False

	def run(self):
		self.is_running = True
		debug_log( 'startup at ', datetime.now() )

		while self.is_running:
			if self.is_business_hours() == False or self.did_error:
				debug_log('sleeping')
				time.sleep(60*5) # Sleep for 5 min
				self.error_check()
				continue
			
			self.build_queue()
			
			if len(self.job_list) < 1:
				debug_log('no jobs')
				time.sleep(30)
			else:
				for job in self.job_list:
					# we don't want to run 90 jobs after an error happened
					self.error_check()
					
					if self.did_error:
						break

					self.run_job(job)