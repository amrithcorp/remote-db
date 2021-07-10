from flask import Flask,request,render_template,url_for,redirect,jsonify
import json 
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import os
import datetime
import re
import requests
from werkzeug.wrappers import response

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "uri"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(25),nullable = False,unique = True)
    password = db.Column(db.String(25),nullable = False)
    is_admin = db.Column(db.Boolean,nullable = False, default = True)
    databases = db.relationship('Database',backref = 'owner')
    jobs = db.relationship('Job',backref = 'owner')

class Job(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)
    db_id = db.Column(db.Integer,db.ForeignKey('database.id'),nullable = False)
    is_grabbed = db.Column(db.Boolean,nullable = False, default = False)
    is_fulfilled = db.Column(db.Boolean,nullable = False, default = False)
    datetime = db.Column(db.DateTime,nullable = False, default = datetime.datetime.utcnow)
    statement = db.Column(db.String(100),nullable = False)

class Database(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable = False)
    db_name = db.Column(db.String(25),nullable = False)
    is_init = db.Column(db.Boolean,default = False)
    jobs = db.relationship('Job',backref = 'dbs')



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
                    owner = User.query.filter_by(username = username).first()
                    new_job = Job(owner = owner,
                                db_id = database_to_write.id,
                                statement = sql)
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
    response = {}
    response["CREATE"] = []
    response["SQL"] = []
    normal_jobs = Job.query.filter_by(is_fulfilled = False)
    for job in normal_jobs:
        u = job.owner
        d = job.dbs
        time = job.datetime
        response["SQL"].append({
            "username" : u.username,
            "password" : u.password,
            "db_name" : d.db_name,
            "time" : time.__str__(),
            "sql_statement" : job.statement
        })
    create_jobs = Database.query.filter_by(is_init = False)
    for job in create_jobs:
        u = job.owner
        d = job.db_name
        response["CREATE"].append({
            "user" : u.username,
            "password" : u.password,
            "database_name" : d,
        })
    return jsonify(response)
@app.route('/update',methods = ["POST"])
def get_verif():
    response = request.json()
    return "recv'd"


@app.route('/new_db/<username>/<password>/<new_db_name>')
def new_db(username,password,new_db_name):
    query = User.query.filter_by(username = username,password = password).first()
    new_database = Database(
        owner = query,
        db_name = new_db_name
    )
    db.session.add(new_database)
    db.session.commit()
    return f"commited {new_db_name} to query!"



if __name__ == "__main__":
    app.run(debug=True)
