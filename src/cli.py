import secrets
import sys
import argparse
import datetime
import sqlite3
import string
import time
import random
import msgpack

parser = argparse.ArgumentParser(description='Client for database')
parser.add_argument('--key', help='generate new login key', action="store_true")
parser.add_argument('--data', help='generate random data', action="store_true")

random.seed(time.time())
args = parser.parse_args()

if args.key:
    db = sqlite3.connect("dashboard.db")
    cur = db.cursor()
    alphabet = string.ascii_uppercase + string.digits
    secret_key = ''.join(secrets.choice(alphabet) for i in range(5))
    end_date = datetime.datetime.now() + datetime.timedelta(hours=24)
    timestamp = datetime.datetime.timestamp(end_date)
    cur.execute("INSERT INTO login_keys (TIMESTAMP, KEY) VALUES(:time, :key)",
            {"time":int(timestamp), "key":secret_key})
    db.commit()
    db.close()
    print(secret_key)

if args.data:
    db = sqlite3.connect("dashboard.db")
    cur = db.cursor()

    for I in range(0, 1000):
        timestamp = time.time_ns()
        device_id = 1
        data = msgpack.packb([random.randint(-1000, 1000)])
        cur.execute("INSERT INTO samples( device_id, timestamp, data ) \
                VALUES (:device_id, :timestamp, :data)", {
                        "device_id" : device_id,
                        "timestamp" : timestamp,
                        "data" : data
                    })


    db.commit()
    db.close()
