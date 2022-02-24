import sqlite3
import numpy
from pathlib import Path
import random
import time
import uuid

sql_file = Path("./db.sql")
database_file = Path("./samples.db")

class devices:
    def __init__(self):
        random.seed(time.time_ns())
        self.devices = list()
        self.counts = dict()

    def create_device(self):
        new_device_id = random.randint(1, 2**63 - 1)
        while new_device_id in self.devices:
            new_device_id = random.randint(1, 2**63 - 1)
        self.devices.append(new_device_id)
        self.counts[new_device_id] = 0
        return new_device_id

    def add_device(self, device_id, initial_count = 0):
        # Check if device exists
        self.devices.append(device_id)
        self.counts[device_id] = initial_count

    def remove_device(self, device_id):
        # Check if device exists
        self.devices.remove(device_id)
        self.counts.remove(device_id)

    def update_count(self, device_id, count):
        # Check if device exists
        self.counts[device_id] = count

    def get_count(self, device_id):
        # Check if device exists
        return self.counts[device_id]

class database:
    def __init__(self, path):
        database_exists = database_file.exists()
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

        if not database_exists:
            with open(sql_file, 'r') as File:
                self.cur.executescript(File.read())

        self.devices = devices()
        # Check for initial devices in database
        db_dev = self.cur.execute("SELECT device_id FROM devices;").fetchall()
        db_dev = [ x[0] for x in db_dev ]
        for I in db_dev:
            statement = f"SELECT id FROM samples WHERE device_id={I} ORDER BY id DESC;"
            self.cur.execute(statement)
            count = self.cur.fetchone()
            if count == None:
                self.devices.add_device(I)
            else:
                self.devices.add_device(I, count[0])

    def new_device(self, name):
        # parse string for allowed characters
        if '"' in name:
            return -1
        elif "'" in name:
            return -1

        new_device_id = self.devices.create_device()

        statement = f"INSERT INTO devices VALUES ({new_device_id}, '{name}');"
        self.cur.execute(statement)
        self.con.commit()

        return (new_device_id, name)

    def change_device_name(self, device_id, name):
        # Check if device exists
        statement = f"UPDATE devices SET name='{name}' WHERE device_id={device_id};"
        self.cur.execute(statement)
        self.con.commit()

    def get_device_id(self, name):
        statement = f"SELECT device_id FROM devices WHERE name='{name}';"
        device_id = self.cur.execute(statement).fetchone();
        return device_id[0]

    def write_sample(self, current, voltage, device_id):
        # Check if current is a float
        if not isinstance(current, float):
            return -1
        # Check if voltage is a float
        if not isinstance(voltage, float):
            return -1
        # Check if device_id exists
        
        # Get timestamp
        origin_time = time.time_ns()
        time_sec = int(origin_time / 1000000000)
        time_usec = int((origin_time / 1000) % 1000000)

        sample_count = self.devices.get_count(device_id) + 1
        unique = str(uuid.uuid4())

        statement = f"INSERT INTO samples VALUES ('{unique}',{sample_count},\
        {device_id},{time_sec},{time_usec},{current},{voltage});"
        self.cur.execute(statement)
        self.con.commit()
        self.devices.update_count(device_id, sample_count)

    def get_samples(self, count, device_id=None):
        pass

    def close(self):
        self.con.close()

a = database(database_file)
device = a.new_device("test")
device2 = a.new_device("test 2")
device3 = a.new_device("test 3")
for I in range(10):
    a.write_sample(float(random.randint(0, 100)), float(random.randint(0,100)),device[0])
    a.write_sample(float(random.randint(0, 100)), float(random.randint(0,100)),device2[0])
    a.write_sample(float(random.randint(0, 100)), float(random.randint(0,100)),device3[0])
a.close()
