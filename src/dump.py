import sqlite3
import msgpack
import csv
from datetime import datetime

with sqlite3.connect("dashboard.db") as con:
    with open("nano.csv", "w") as file:
        writer = csv.writer(file)
        cur = con.cursor()
        cur.execute("SELECT timestamp, data FROM samples WHERE device_id=4")

        data = cur.fetchall()

        length = len(data)
        for i in range(0, len(data)):
            print("Written ", i, "/", length)
            out = list()
            timestamp = datetime.fromtimestamp(data[i][0] / 1000000000.0).strftime("%Y/%m/%d %H:%M:%S.%f")
            unpacked = msgpack.unpackb(data[i][1])
            out.append(timestamp)
            out.extend(unpacked)
            writer.writerow(out)
