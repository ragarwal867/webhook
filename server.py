# Starts on port 5000, built on Flask, so check Flash config to customize
# Creates folders for each of the inboxes and puts the messages received into a file (down to a ms accuracy)
# Loads every inbox and every request into memory at run-time. Delete old inboxes if they aren't used any more
# Can be run using `python3 webhook.py`
# Common routes
# http://localhost:5000 -> To check if server is up
# http://localhost:5000/list -> To list all inboxes
# http://localhost:5000/send/inbox0001 [POST] -> To send a payload to inbox named inbox0001
# http://localhost:5000/view/inbox0001 -> To view items on inbox named inbox0001

from typing import OrderedDict
from flask import request
from flask import Flask
import os
import time
import json
from collections import OrderedDict
import threading

app = Flask(__name__)

config = {}
inboxes = set()
round_robin_counter = 0

responseBodyArray = [
    {
        "code": "601",
        "error": {
            "type": "FORBIDDEN",
            "message": "Incorrect number of variables for the template provided"
        }
    },
    {
        "code": "602",
        "error": {
            "type": "FORBIDDEN",
            "message": "Incorrect number of variables for the template provided"
        }
    },
    {
        "code": "603",
        "error": {
            "type": "FORBIDDEN",
            "message": "Maximum length limit for string variables (30) exceeded"
        }
    },
    {
        "code": "604",
        "error": {
            "type": "FORBIDDEN",
            "message": "URL is invalid, make sure you are providing valid protocol and host"
        }
    },
    {
        "code": "605",
        "error": {
            "type": "FORBIDDEN",
            "message": "The template with similar values is already registered"
        }
    },
    {
        "code": "606",
        "error": {
            "type": "FORBIDDEN",
            "message": "The provided MSISDN is invalid"
        }
    },
    {
        "code": "607",
        "error": {
            "type": "FORBIDDEN",
            "message": "An invalid token was provided"
        }
    } 
] 

def setup():
    global inboxes
    # Create the inboxes directory
    os.makedirs("./inboxes", exist_ok=True)
    inboxes = set(os.listdir("./inboxes/"))

def create_inbox(inbox):
    global inboxes
    os.makedirs(os.path.join("inboxes", inbox), exist_ok=True)
    inboxes.add(inbox)


def get_response_body():
    global round_robin_counter
    response_body = responseBodyArray[round_robin_counter % len(responseBodyArray)]
    round_robin_counter += 1
    return response_body

@app.route('/')
def hello_world():
    return 'Webhook is UP'

@app.route('/send/<inbox>', methods=['POST'])
def send_data(inbox):
    print(request.data)
    response_body = get_response_body()
    return response_body, 403, {'Content-Type': 'application/json'}

@app.route('/list')
def list_inboxes():
    return {"data" : list(inboxes)}

@app.route('/view/<inbox>')
def view_inbox(inbox):
    output = OrderedDict()
    for file in sorted(os.listdir(os.path.join("inboxes", inbox)), reverse=True):
        if file == "." or file == "..":
            continue
        with open(os.path.join("inboxes", inbox, file)) as h:
            content = h.read()
            try:
                contentJson = json.loads(content)
                output[time.ctime(int(file)/1000) + "." + str(int(file)%1000)] = contentJson
            except Exception as e:
                output[time.ctime(int(file)/1000) + "." + str(int(file)%1000)] = content
    return output

def scan_config():
    global config
    try:
        new_config = {}
        with open("config.json") as file:
            new_config = json.load(file)
            updated = False
            if new_config != config:
                print("Updated configuration at " + str(time.time()))
            config = new_config
    except FileNotFoundError as e:
        print("config.json not found")
        pass

def interval_function():
    while True:
        time.sleep(10)
        scan_config()

if __name__ == '__main__':
    scan_config()
    threading.Thread(target=interval_function).start()
    setup()
    app.run()
