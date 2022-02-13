from flask import Flask, url_for, request, render_template, redirect, send_from_directory, jsonify, Response, make_response, abort
from werkzeug.utils import secure_filename
import os
import secrets
from datetime import datetime
from pysondb import db

app = Flask(__name__)

ALLOWED_EXTENSIONS = set(["txt", "jpg", "png", "zip", "mp4"])
global databaseFile, usersDB
databaseFile = "data.json"
usersDB = "users.json"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def jsondb_getall(databaseFile):
    database=db.getDb(databaseFile)
    return database.getAll()

def jsondb_get(databaseFile, data):
    database=db.getDb(databaseFile)
    return database.getByQuery(data)

def jsondb_insert(databaseFile, data):
    database=db.getDb(databaseFile)
    return database.add(data)

def jsondb_delete(databaseFile, id):
    database=db.getDb(databaseFile)
    return database.deleteById(id)

def jsondb_update(databaseFile, id, data):
    database=db.getDb(databaseFile)
    return database.updateById(id,data)

def index(name):
    UserTokenCookie = request.cookies.get('UserToken')
    UserCookie = request.cookies.get('User')
    UserData = jsondb_get(usersDB, { "username": UserCookie, "token": UserTokenCookie} )
    if UserTokenCookie and UserCookie and UserData:
        UserToken = UserData[0]["token"]
        User = UserData[0]["name"]
        if UserData and UserToken != UserTokenCookie and User != UserCookie:
            logout()
    else:
        logout()
        UserToken = False
        User = False
    return render_template("index.html", name=name, userSession=UserToken, user=User)


def form():
    return render_template("form.html")

def upload():
    folder = "uploads"
    file = request.files['uploadFile']
    filename = secure_filename(file.filename)

    if file and allowed_file(file.filename):
        file.save(os.path.join(folder, filename))
  
        today = datetime.today()  
        msg  = 'File successfully uploaded ' + file.filename
    else:
        msg  = 'Invalid File Format'
    return jsonify({'htmlresponse': render_template('response.html', msg=msg, uploaded_file=filename)})

def logout():
    resp = make_response()
    resp.delete_cookie('User')
    resp.delete_cookie('UserToken')
    return resp

def api():
    data = request.form
    methode = request.method

    match methode:
        case "GET":
            return jsonify(jsondb_getall())

        case "POST":
            type = data["type"]

            match type:
                case "register":
                    name = data["name"]
                    username = data["username"]
                    password = data["password"]

                    if username == "" or password == "" or name == "":
                        return abort(400)
                    checkUsername = jsondb_get(usersDB, { "username": username } )
                    if checkUsername and checkUsername[0]["username"] == username:
                        return abort(403)
                    else:
                        data = { "name": name, "username": username, "password": password, "token": secrets.token_urlsafe(32), "state": True }
                        jsondb_insert(usersDB, data)
                        return ""

                case "login":
                    username = data["username"]
                    password = data["password"]

                    try:
                        staylogged = data["staylogged"]
             
                    except KeyError:
                        staylogged = False
    
                    data = {"username": username, "password": password}

                    if username == "" or password == "":
                        return abort(400)
                        
                    resp = make_response()
                    getAuth = jsondb_get(usersDB, data)

                    if (getAuth and getAuth[0]["password"] == password):

                        if staylogged:
                            resp.set_cookie('User', username, 2147483647, "/")
                            resp.set_cookie('UserToken', getAuth[0]["token"], 2147483647,"/")
                            return resp
                        else:
                            resp.set_cookie('User', username, None, "/")
                            resp.set_cookie('UserToken', getAuth[0]["token"], None,"/")
                            return resp
                    else:
                        return abort(403)
                        
                case "logout":
                    return logout()

                case "add":
                    name = data["name"]
                    data = {"name":name,"state":True}
                    jsondb_insert(data)
                    return name + " added"
                    
                case "update":
                    id = data["id"]
                    data = data["data"]
                    #database.update({"name":"Pyson-CLI"},{"name":"PysonCLI"})
                    data = {"name":data}
                    jsondb_update(id, data)
                    return data + " updated"
    
        case "DELETE":
            id = data["id"]
            jsondb_delete(id)
            return id + " deleted"

@app.route('/',methods=["GET"])
@app.route('/<route>',methods=["POST","PUT","GET","DELETE","PATCH"])
def route(route=None):
    match route:
        case None:
            name = "Tolle Webseite mit Flask (Python)"
            return index(name)
        case "api":
            return api()
        case "upload":
            return upload()
        case "form":
            return form()
        case "main":
            return render_template('pages/main.html')

if __name__ == "__main__":
    app.run(port=1337, debug=True)
