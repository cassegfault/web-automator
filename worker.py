from autoscraper import Automator
import sys
import signal
import json


# This program only accepts one option, the configuration file
config_filename = 'config.json'
if len(sys.argv) > 1:
	config_filename = sys.argv[1]

config = {}
try:
	with open(config_filename) as config_file:
		config = json.load(config_file)
		config['filename'] = config_filename
except IOError:
	print("There was an error opening the configuration file: ", config_filename)
	sys.exit()


b = Automator(config_filename)
b.run()

def handler(signum, frame):
	b.quit()
	sys.exit()

signal.signal(signal.SIGINT, handler)

