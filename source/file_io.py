import json
import datetime
import time

#writes data object to json file fileName at path
#overwrites all data currently in the file
def writeToFile(path, data):
    with open(path, 'w') as fp:
        fp.write(data)

#reads and returns all data in fileName at path
def readFile(path):
    with open(path, 'r') as fp:
        return fp

#writes data to txt file fileName at path
def appendToFile(path, data):
    with open(path, 'a') as fp:
        fp.write('\n' + data)

#fetch json file at path
def fetchJSON(path):
    with open(path, 'r') as f:
        data = json.load(f)
        return data

#get current timestamp
def getTimestamp():
    today = datetime.date.today()
    date = today.strftime("%m/%d/%Y")
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return date + " " + current_time