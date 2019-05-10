import unittest
from scraperAPI import ScraperAPI
import sqlite3
import os

class TestAPI(unittest.TestCase):
    __temp_db_filename = 'tests/temp.db'
    API = None
    
    @classmethod
    def setUpClass(cls):
        # Get a connection to the database
        conn = sqlite3.connect(cls.__temp_db_filename)
        c = conn.cursor()

        # Build the tables necessary to run tests
        c.execute("CREATE TABLE errors (id int, error text)")
        c.execute("CREATE TABLE task_logs (id int, log_json json, task_id int)")
        c.execute("CREATE TABLE requests (id int, url text, task_id int, sent_by text)")
        c.execute("CREATE TABLE tasks (id int, date_started int, date_completed int)")

        # instantiate the API with an in-memory sqlite database
        cls.API = ScraperAPI(config_json={ 'db_filename': 'tests/temp.db' })

    def test_inserts(self):
        # testing error and request types, all types derive from the same base class
        request_items = [{ 'url':'testing_this.com/test1' },
                                { 'url':'testing_this.com/test2' },
                                { 'url':'testing_this.com/test3' }]
        error_item = { 'error': 'Testing the error system' }
        self.API.error.insert(error_item)
        self.API.request.insert_many(request_items)
        errors = self.API.error.get_all()
        requests = self.API.request.get_all()
        
        # assert the right number are being inserted
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(requests), 3)

        # assert the insertions are passing data properly
        self.assertIn(errors[0]['error'], [row['error'] for row in errors])
        self.assertIn(requests[0]['url'], [row['url'] for row in requests])
    
    @classmethod
    def tearDownClass(cls):
        os.remove(cls.__temp_db_filename)

if __name__ == '__main__':
    unittest.main()