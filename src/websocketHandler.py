import base

import bcrypt
import re

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket

import secrets

import time
import calendar

import base64
import aiosqlite
import msgpack
import asyncio

import json
import datetime

class BaseWebSocketHandler(tornado.websocket.WebSocketHandler):
    def row_to_obj(self, row, cur):
        obj = tornado.util.ObjectDict()
        for val, desc in zip(row, cur.description):
            obj[desc[0]] = val
        return obj

    async def query(self, stmt, kwargs):
        async with (await self.application.db.cursor()) as cur:
            await cur.execute(stmt, kwargs)
            return [self.row_to_obj(row, cur) for row in await cur.fetchall()]

    async def get_user_from_device(self, device_id):
        statement = "SELECT * FROM devices WHERE device_key=:device_id"
        result = await self.query(statement, {"device_id":device_id})
        if len(result) == 0:
            return 0
        elif len(result) > 1:
            return 0
        else:
            return result[0].user_id

    async def get_user_from_api(self, api_key):
        statement = "SELECT * FROM api_keys WHERE key=:api_key"
        result = await self.query(statement, {"api_key":api_key})
        if len(result) == 0:
            return 0
        elif len(result) > 1:
            return 0
        else:
            return result[0].user_id

    async def write_samples(self, data, device_id):
        count = len(data["timestamp"])

        statement = "SELECT (id) FROM devices WHERE device_key=:device_key"
        device_id = await self.query(statement, {"device_key": device_id})
        device_id = device_id[0].id

        statement = "INSERT INTO samples (device_id, timestamp, data)\
                VALUES (:device_id, :timestamp, :data)"
        for i in range(0, count):
            i_data = list()
            for key,val in data["data"].items():
                i_data.append(val[i])
                
            await self.query(statement, {
                    "device_id": device_id,
                    "timestamp": data["timestamp"][i],
                    "data" : msgpack.packb(i_data)
                })
        await self.application.db.commit()

class DeviceHandler(BaseWebSocketHandler):
    channels = set()

    def initialize(self):
        self.device_id = 0
        self.user_id = 0
        self.unpacker = msgpack.Unpacker()
        self.fields = list()

    async def open(self, device_id):
        print("connection requested")
        await asyncio.sleep(0.5)
        self.channels.add(self)
        self.user_id = await self.get_user_from_device(device_id)
        if self.user_id == 0:
            await self.write_message("NOK")
            self.close()
        else:
            self.device_id = device_id
            statement = "SELECT * FROM devices WHERE device_key=:device_key"
            device = await self.query(statement, {"device_key" : device_id})
            device = device[0]
            statement = "SELECT * FROM device_fields WHERE device_id=:id"
            fields = await self.query(statement, {"id": device.id})
            for I in fields:
                single_result = dict()
                single_result["field_type"] = I.field_type
                single_result["field_name"] = I.field_name
                self.fields.insert( I.field_index, single_result )
            print(fields)
            await self.write_message("OK")

    async def on_message(self, message):
        print("got data")
        server = tornado.ioloop.IOLoop.current()
        data = base64.b64decode(message)
        self.unpacker.feed(data)
        for o in self.unpacker:
            timestamps = list()
            for I in o[0]:
                timestamps.append(time.time_ns())
            result = dict()
            result["timestamp"] = timestamps
            result["data"] = dict()
            for I in range(0, len(self.fields)):
                result["data"][self.fields[I]["field_name"]] = o[I]

            print(result)
            await self.write_samples(result, self.device_id)
            server.add_callback(ClientHandler.send_message,
                            self.user_id, self.device_id,
                            result)

    def on_close(self):
        print("connection closed")
        self.channels.remove(self)

    def check_origin(self, origin):
        return True

class ClientHandler(BaseWebSocketHandler):
    channels = set()

    def initialize(self):
        self.user_id = 0
        self.devices = list()

    async def open(self):
        await asyncio.sleep(0.5)
        if not self.get_secure_cookie(self.application.cookie_name):
            return
        self.channels.add(self)
        self.user_id = self.get_secure_cookie(self.application.cookie_name).decode('utf-8')
        self.user_id = self.application.user_sessions[self.user_id]

    async def on_message(self, message):
        split = message.split(" ")
        if split[0] == "ADD":
            check = await self.get_user_from_device(split[1])
            if check != 0:
                print("Adding new device")
                self.devices.append(split[1])
        elif split[0] == "DEL":
            check = await self.get_user_from_device(split[1])
            if check != 0:
                self.devices.remove(split[1])

    @classmethod
    async def send_message(cls, user_id, device_id, message):
        print("sending message")
        channel = None
        for I in cls.channels:
            if I.user_id == user_id:
                channel = I
                break;
        if channel == None:
            return
        if device_id in channel.devices:
            for key,value in message["data"].items():
                message[key] = value
            message.pop("data")
            json_dump = json.dumps({ device_id : message })
            await channel.write_message(json_dump)

    def on_close(self):
        self.channels.remove(self)

    def check_origin(self, origin):
        return True

def handlers():
    return [
        (r"/device/(.*?)", DeviceHandler),
        (r"/client", ClientHandler),
        ]
