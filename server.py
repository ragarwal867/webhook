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

def setup():
    global inboxes
    # Create the inboxes directory
    os.makedirs("./inboxes", exist_ok=True)
    inboxes = set(os.listdir("./inboxes/"))

def create_inbox(inbox):
    global inboxes
    os.makedirs(os.path.join("inboxes", inbox), exist_ok=True)
    inboxes.add(inbox)

def get_response_code():
    global round_robin_counter
    response_codes = config.get("response_codes", [200])
    response_code = response_codes[round_robin_counter % len(response_codes)]
    round_robin_counter += 1
    return response_code

@app.route('/')
def hello_world():
    return 'Webhook is UP'

@app.route('/send/<inbox>', methods=['POST'])
def send_data(inbox):
    print(request.data)
    response_code = get_response_code()
    if response_code == 429:
        return 'Error', 429
    elif response_code == 200: 
        create_inbox(inbox)
        msg_file = int(time.time() * 1000)
        h = open(os.path.join('inboxes', inbox, str(msg_file)), 'wb')
        h.write(request.data)
        h.close()
        return 'OK'

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
    app.run(host="0.0.0.0")
