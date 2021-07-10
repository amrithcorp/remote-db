import sqlite3
import requests
import json
from time import sleep
import os

# fbe is the username, AOF... is the drive, stpdsql is the directory

drive_path = "/media/fbe/A0FEFD5DFEFD2BE2/stpdsql/"

token = "admin_token"

update_url = "http://127.0.0.1:5000/update"
jobs_url  = "http://127.0.0.1:5000/query_jobs"

req = requests.get(jobs_url)

parsed_req = json.loads(req.text)


def create_db(username,password,name):
    path = f"{drive_path}{username}"

    db_path = f"{path}/{name}.sqlite3"
    
    if not os.path.exists(path):
        os.makedirs(path)
        con = sqlite3.connect(db_path)
        return db_path
    else:
        con = sqlite3.connect(db_path)


def run_jobs(new_request):
    all = {}
    for i in parsed_req["CREATE"]:
        username = i["user"]
        password = i["password"]
        name = i["database_name"]
        create_db(username,password,name)
        data = {
            "type" : "create_db",
            "db_name" : name,
            "is_init" : True
        }
        response = requests.post(url = update_url, data = data)
    for i in parsed_req["SQL"]:
        username = i["username"]
        password = i["password"]
        db_name = i["db_name"]
        time_date = i["time"]
        sql = i["sql_statement"]
        db_path = f"{drive_path}{username}/{db_name}"
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        try:
            cur.execute(sql)
            print(cur.fetchall())
            data = {
                "type" : "sql",
                "db" : db_name,
                "sql" : sql,
                "user" : username,
                "password" : password,
                "is_grabbed" : True,
                "is_done" : True,
                "is_working" : True
            }
            response = requests.post(url = update_url, data = data)            
        except sqlite3.OperationalError as s:
            data = {
                "type" : "sql",
                "db" : db_name,
                "sql" : sql,
                "user" : username,
                "password" : password,
                "is_grabbed" : True,
                "is_done" : False,
                "is_working" : False,
                "error" : str(s)
            }
            print(json.dumps(data))
            response = requests.post(url = update_url, json = data)            

run_jobs(parsed_req)
