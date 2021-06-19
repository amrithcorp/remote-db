from flask import Flask,request,render_template,url_for,redirect,jsonify
import json 
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import os
import datetime
import re
import requests
from werkzeug.wrappers import response
# uri = os.getenv("DATABASE_URL")  # or other relevant config var
# if uri.startswith("postgres://"):
#     uri = uri.replace("postgres://", "postgresql://", 1)
#rest of connection code using the connection string `ur

uri = "postgresql://jhlavouwqmjxxm:48c0476817e35bdf8c30c7af5cba4909980f020681f514b11b24a020eeddeb8e@ec2-54-225-228-142.compute-1.amazonaws.com:5432/dbqjib6769mtga"

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(25),nullable = False,unique = True)
    password = db.Column(db.String(25),nullable = False)
    is_admin = db.Column(db.Boolean,nullable = False, default = True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer,nullable = False)
    db_id = db.Column(db.Integer)
    is_grabbed = db.Column(db.Boolean,nullable = False, default = False)
    datetime = db.Column(db.DateTime,nullable = False, default = datetime.datetime.utcnow)
    statement = db.Column(db.String(100),nullable = False)

class Database(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer)
    db_name = db.Column(db.String(25),nullable = False)
    is_init = db.Column(db.Boolean,default = False)

class Create(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    database_id = db.Column(db.Integer)
    is_grabbed = db.Column(db.Boolean,default = False)
    is_created = db.Column(db.Boolean,default = False)


@app.route('/')
def index():
    return (redirect(url_for("signup")))

@app.route('/signup',methods = ["GET","POST"])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")
    else:
        username = request.form["username"]
        password = request.form["password"]
        new_account = User(username = username,
                           password = password)
        db.session.add(new_account)
        db.session.commit()
        account = User.query.filter_by(username = username,password = password).first()
        new_db_name = account.username + "_db"
        new_database = Database(user_id = account.id,
                                db_name = new_db_name)
        db.session.add(new_database)
        db.session.commit()
        created_database = Database.query.filter_by(db_name = new_db_name).first()
        new_db_create_fun = Create(database_id = created_database.id)
        db.session.add(new_db_create_fun)
        db.session.commit() 
        return f"created account and database at {new_db_name}"


@app.route('/send_query/<username>/<password>/<db_name>/',methods = ["GET","POST"])
def query(username,password,db_name):
    if request.method == 'GET':
        return "Post query to here!"
    else:
        sql = (request.get_json())["sql"]
        user_info = User.query.filter_by(username = username).first()
        try:
            # authentication
            correct_password = user_info.password
            if correct_password == password:
                try:
                    # find the database
                    database_to_write = Database.query.filter_by(db_name = db_name).first()
                    # create the job
                    new_job = Job(user_id = user_info.id,
                                db_id = database_to_write.id,
                                statement = sql                       
                                )
                    db.session.add(new_job)
                    db.session.commit()
                    return "cool beans!"
                except:
                    return "no such database"
            else: 
                return "bad password"
        except:
            return "username or password bad"
        
@app.route('/query_jobs',methods = ["GET"]) #<token>
def admin(): #token
    jobs = {}
    jobs["CREATE"] = []
    jobs["SQL"] = []
    new_jobs_query = Job.query.filter_by(user_id = 1).all()
    new_create_query = Create.query.filter_by(is_created = False).all()
    for i in new_create_query:
        print(i.db_id)
    for i in new_jobs_query:
        i.is_grabbed = True
        print(i.user_id)
        from_account = User.query.filter_by(id = i.user_id).first()
        for_database = Database.query.filter_by(id = i.db_id).first()
        jobs["SQL"].append({
            "username" : from_account.username,
            "db_name" : for_database.db_name,
            "time" : i.datetime,
            "sql_statement" : i.statement
        })
        db.session.commit()      
    return jsonify(jobs)

@app.route('/update',methods = ["POST"])
def get_verif():
    response = request.get_json()
    created_databases = response["CREATED_DB"]
    for i in created_databases:
        print(i)

if __name__ == "__main__":
    app.run(debug=True)