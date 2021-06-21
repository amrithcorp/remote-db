import sqlite3
import requests
import json
from time import sleep as sl

query_jobs = "http://127.0.0.1:5000/query_jobs"

drive_path = "/media/fbe/A0FEFD5DFEFD2BE2/stpdsql/"

#while True:
#    pass

def get_queries():
    r = requests.get(query_jobs)
    return json.loads(r.text)

print(get_queries())