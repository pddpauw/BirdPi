import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

def connect_to_db():
    userDir = os.path.expanduser('~')
    conn = sqlite3.connect(userDir + '/BirdNET-Pi/scripts/birds.db')
    return conn


def get_detections():
    detections = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM detections ORDER BY Date DESC, Time DESC")
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            detection = {}
            detection["Date"] = i["Date"]
            detection["Time"] = i["Time"]
            detection["Sci_Name"] = i["Sci_Name"]
            detection["Com_Name"] = i["Com_Name"]
            detection["Confidence"] = i["Confidence"]
            detection["Lat"] = i["Lat"]
            detection["Lon"] = i["Lon"]
            detection["Cutoff"] = i["Cutoff"]
            detection["Week"] = i["Week"]
            detection["Sens"] = i["Sens"]
            detection["Overlap"] = i["Overlap"]
            detection["File_Name"] = i["File_Name"]
            detection["Manual_ID"] = i["Manual_ID"]
            detections.append(detection)

    except:
        detections = []

    return detections 


def get_detections_by_com_name(com_name):
    detections = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM detections WHERE Com_Name LIKE ?", (com_name,))
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            detection = {}
            detection["Date"] = i["Date"]
            detection["Time"] = i["Time"]
            detection["Sci_Name"] = i["Sci_Name"]
            detection["Com_Name"] = i["Com_Name"]
            detection["Confidence"] = i["Confidence"]
            detection["Lat"] = i["Lat"]
            detection["Lon"] = i["Lon"]
            detection["Cutoff"] = i["Cutoff"]
            detection["Week"] = i["Week"]
            detection["Sens"] = i["Sens"]
            detection["Overlap"] = i["Overlap"]
            detection["File_Name"] = i["File_Name"]
            detection["Manual_ID"] = i["Manual_ID"]
            detections.append(detection)

    except:
        print("shit")
        detections = []

    return detections 

def get_detections_by_sci_name(sci_name):
    detections = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM detections WHERE Sci_Name LIKE ?", (sci_name,))
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            detection = {}
            detection["Date"] = i["Date"]
            detection["Time"] = i["Time"]
            detection["Sci_Name"] = i["Sci_Name"]
            detection["Com_Name"] = i["Com_Name"]
            detection["Confidence"] = i["Confidence"]
            detection["Lat"] = i["Lat"]
            detection["Lon"] = i["Lon"]
            detection["Cutoff"] = i["Cutoff"]
            detection["Week"] = i["Week"]
            detection["Sens"] = i["Sens"]
            detection["Overlap"] = i["Overlap"]
            detection["File_Name"] = i["File_Name"]
            detection["Manual_ID"] = i["Manual_ID"]
            detections.append(detection)

    except:
        print("shit")
        detections = []

    return detections 

def get_detections_by_date(date):
    detections = []
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM detections WHERE DATE LIKE ? ORDER BY Time Desc", (date,))
        rows = cur.fetchall()

        # convert row objects to dictionary
        for i in rows:
            detection = {}
            detection["Date"] = i["Date"]
            detection["Time"] = i["Time"]
            detection["Sci_Name"] = i["Sci_Name"]
            detection["Com_Name"] = i["Com_Name"]
            detection["Confidence"] = i["Confidence"]
            detection["Lat"] = i["Lat"]
            detection["Lon"] = i["Lon"]
            detection["Cutoff"] = i["Cutoff"]
            detection["Week"] = i["Week"]
            detection["Sens"] = i["Sens"]
            detection["Overlap"] = i["Overlap"]
            detection["File_Name"] = i["File_Name"]
            detection["Manual_ID"] = i["Manual_ID"]
            detections.append(detection)

    except:
        print("shit")
        detections = []

    return detections 

def update_user(user):
    updated_user = {}
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET name = ?, email = ?, phone = ?, address = ?, country = ? WHERE com_name =?", (user["name"], user["email"], user["phone"], user["address"], user["country"], user["com_name"],))
        conn.commit()
        #return the user
        updated_user = get_detections_by_com_name(user["com_name"])

    except:
        conn.rollback()
        updated_user = {}
    finally:
        conn.close()

    return updated_user


def delete_user(com_name):
    message = {}
    try:
        conn = connect_to_db()
        conn.execute("DELETE from users WHERE com_name = ?", (com_name,))
        conn.commit()
        message["status"] = "User deleted successfully"
    except:
        conn.rollback()
        message["status"] = "Cannot delete user"
    finally:
        conn.close()

    return message


users = []
user0 = {
    "name": "Charles Effiong",
    "email": "charles@gamil.com",
    "phone": "067765665656",
    "address": "Lui Str, Innsbruck",
    "country": "Austria"
}

user1 = {
    "name": "Sam Adebanjo",
    "email": "samadebanjo@gamil.com",
    "phone": "098765465",
    "address": "Sam Str, Vienna",
    "country": "Austria"
}

user2 = {
    "name": "John Doe",
    "email": "johndoe@gamil.com",
    "phone": "067765665656",
    "address": "John Str, Linz",
    "country": "Austria"
}

user3 = {
    "name": "Mary James",
    "email": "maryjames@gamil.com",
    "phone": "09878766676",
    "address": "AYZ Str, New york",
    "country": "United states"
}

users.append(user0)
users.append(user1)
users.append(user2)
users.append(user3)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/api/detections', methods=['GET'])
def api_get_detections():
    return jsonify(get_detections())

@app.route('/api/detections/date/<date>', methods=['GET'])
def api_get_detections_by_date(date):
    return jsonify(get_detections_by_date(date))

@app.route('/api/species/com/<com_name>', methods=['GET'])
@app.route('/api/species/<com_name>', methods=['GET'])
def api_get_detections_by_com_name(com_name):
    return jsonify(get_detections_by_com_name(com_name))

@app.route('/api/species/sci/<sci_name>', methods=['GET'])
def api_get_detections_by_sci_name(sci_name):
    return jsonify(get_detections_by_sci_name(sci_name))

@app.route('/api/users/add',  methods = ['POST'])
def api_add_user():
    user = request.get_json()
    return jsonify(insert_user(user))

@app.route('/api/users/update',  methods = ['PUT'])
def api_update_user():
    user = request.get_json()
    return jsonify(update_user(user))

@app.route('/api/users/delete/<com_name>',  methods = ['DELETE'])
def api_delete_user(com_name):
    return jsonify(delete_user(com_name))


if __name__ == "__main__":
    #app.debug = True
    #app.run(debug=True)
    app.run()

# Code based on template from https://github.com/effiongcharles/full_stack_web_python_flask_react_bootstrap/blob/main/backend_python_api/api.py
