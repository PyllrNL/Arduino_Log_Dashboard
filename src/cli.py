import secrets
import sys
import argparse
import datetime
import sqlite3
import string

parser = argparse.ArgumentParser(description='Client for database')
parser.add_argument('--key', help='generate new login key', action="store_true")

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

