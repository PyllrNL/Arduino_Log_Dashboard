import tornado.ioloop
import tornado.httpserver
import tornado.web
import base
import json
import secrets

class RestBaseHandler(base.BaseHandler):
    async def check_api_key(self, key):
        if self.get_secure_cookie("arduino_dashboard"):
            return int(self.get_secure_cookie("arduino_dashboard"))
        if key == []:
            return None

        if len(key) > 1:
            return None

        key = key[0]
        statement = "SELECT * FROM api_keys WHERE key=:key"
        results = await self.query(statement, {"key":key})
        if len(results) == 0:
            return None
        elif len(results) > 1:
            return None
        return results[0].user_id

class DeviceBaseHandler(RestBaseHandler):
    async def get(self):
        user_id = await self.check_api_key(self.get_arguments("key"))
        if user_id == None:
            raise HTTPError(403)

        statement = "SELECT * FROM devices WHERE user_id=:user_id"
        results = await self.query(statement, {"user_id":user_id})
        self.set_header("Content-Type", "application/json")
        output = []
        for i in results:
            output.append(i.device_key)
        self.write(json.dumps(output))

    async def post(self):
        user_id = await self.check_api_key(self.get_arguments("key"))
        if user_id == None:
            raise HTTPError(403)
        if self.request.headers['Content-Type'] == 'application/x-json':
            args = json.loads(self.request.body)
            if not args["name"]:
                raise HTTPError(400)
            if not args["fields"]:
                raise HTTPError(400)
            if len(args["fields"]) < 1:
                raise HTTPError(400)
            new_device_key = secrets.token_urlsafe(32)
            statement = "INSERT INTO devices (user_id, name, device_key) VALUES\
                    (:user_id, :name, :device_key) RETURNING id"
            result = await self.query(statement,
                    {"user_id":user_id,
                     "name": args["name"],
                     "device_key": new_device_key})
            statement = "INSERT INTO device_fields (device_id, field_id, field) VALUES\
                    (:device_id, :field_id, :field)"
            print(args["fields"])
            for i in range(0, len(args["fields"])):
                print(i)
                await self.query(statement, {
                        "device_id" : result[0].id,
                        "field_id" : i,
                        "field": args["fields"][i]
                    })
            await self.application.db.commit()

class DeviceSpecificHandler(RestBaseHandler):
    async def get(self, device_key):
        print("yay")
        user_id = await self.check_api_key(self.get_arguments("key"))
        if user_id == None:
            raise HTTPError(403)
        self.set_header("Content-Type", "application/json")
        device = dict()
        statement = "SELECT id, name FROM devices WHERE device_key=:device_key"
        results = await self.query(statement, {"device_key":device_key})
        if len(results) == 0:
            raise HTTPError(400)
        device["name"] = results[0].name
        device_id = results[0].id
        statement = "SELECT field FROM device_fields WHERE device_id=:device_id\
                ORDER BY field_id ASC"
        results = await self.query(statement, {"device_id":device_id})
        device["fields"] = list()
        print(results)
        for I in results:
            device["fields"].append(I.field)
        string = json.dumps(device)
        self.write(string)

def handlers():
    return [
        (r"/api/device", DeviceBaseHandler),
        (r"/api/device/(.*?)", DeviceSpecificHandler),
    ]
