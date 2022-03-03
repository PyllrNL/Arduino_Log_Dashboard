import db
import sys
import argparse

parser = argparse.ArgumentParser(description='Client for database')
parser.add_argument('--name', nargs='?', help='name of new device')

args = parser.parse_args()

if args.name:
    database = db.database(db.database_file)
    key = database.new_device(args.name)
    print(key[0])
