import tornado.ioloop
import tornado.httpserver
import tornado.web
import base
import json
import secrets

class RestBaseHandler(base.BaseHandler):
    def authenticate(self):
        return 1
        #user_key = self.get_secure_cookie(self.application.cookie_name)
        #if user_key == None:
        #    raise tornado.web.HTTPError(403)
        #if user_key not in self.application.user_sessions:
        #    self.redirect("/auth/login")
        #return self.application.user_sessions[user_key]

    def parse_int_argument( self, name, default, minimum, maximum ):
        arg = self.get_argument(name, str(default))
        
        try:
            arg = int(arg)
        except:
            raise tornado.web.HTTPError(400)

        if arg < minimum:
            raise tornado.web.HTTPError(400)

        if maximum > minimum:
            if arg > maximum:
                raise tornado.web.HTTPError(400)

        return arg

    def parse_bool_argument( self, name, default ):
        arg = self.get_argument(name, str(default))

        if arg == "False":
            return False
        elif arg == "True":
            return True
        else:
            raise tornado.web.HTTPError(400)

    def validate_string( self, string ):
        pass

    def validate_field( self, field ):
        allowed_types = ["int", "float", "bool"]
        self.validate_string( field["name"] )

        if field["type"] not in allowed_types:
            raise tornado.web.HTTPError(400)

    def validate_fields( self, fields ):
        for I in fields:
            self.validate_field( I )

    async def get_devices_from_user(self, user_id, limit, page, ascending):
        response = dict()
        statement = "SELECT COUNT(*) from devices where user_id=:user_id"
        result = await self.querycount(statement, {"user_id": user_id})

        div = int(result / limit)
        response["total_pages"] = div if div > 0 else 1
        response["page"] = page
        response["data"] = list()

        if result == 0:
            return response

        retrieve_limit = limit * (page + 1)

        statement = "SELECT * from devices where user_id=:user_id ORDER BY\
                id {} LIMIT {}".format(
                        "ASC" if ascending else "DESC",
                        retrieve_limit)
        
        result = await self.query(statement, {
                "user_id" : user_id,
            })

        for I in range(limit * page, len(result)):
            response["data"].append({ "name" : result[I].name,
                                      "id" : result[I].device_key })

        return response

    async def create_new_device( self, user_id, structure ):
        self.validate_string(structure["name"])
        self.validate_fields(structure["fields"])

        device_key = secrets.token_urlsafe(32)

        statement = "INSERT INTO devices (user_id, name, device_key) VALUES\
                (:user_id, :name, :device_key) RETURNING id"

        result = await self.query(statement, {
                "user_id" : user_id,
                "name" : structure["name"],
                "device_key" : device_key
            })

        device_id = result[0].id

        for I in range(0, len(structure["fields"])):
            statement = "INSERT INTO device_fields (field_index,field_name,\
                    field_type, device_id) VALUES (:index,:name,:type,\
                    :device_id)"
            result = await self.query(statement, {
                    "index": I,
                    "name" : structure["fields"][I]["name"],
                    "type" : structure["fields"][I]["type"],
                    "device_id" : device_id
                })
        await self.application.db.commit()

        structure["id"] = device_key

        return structure

    async def get_device_with_id( self, user_id, device_id ):
        response = dict()

        statement = "SELECT * FROM devices WHERE device_key=:device_key"
        print(device_id)
        result = await self.query(statement, {"device_key" : device_id})

        response["id"] = result[0].device_key
        response["name"] = result[0].name

        statement = "SELECT * FROM device_fields WHERE device_id=:device_id\
                ORDER BY field_index ASC"
        result = await self.query(statement, {
                "device_id" : result[0].id
            })

        response["fields"] = list()
        for I in result:
            response["fields"].append({
                    "type" : I.field_type,
                    "name" : I.field_name
                })

        return response

    async def get_device_with_name( self, user_id, device_name ):
        response = dict()

        statement = "SELECT * FROM devices WHERE name=:name"
        print(device_name)
        result = await self.query(statement, {"name" : device_name})

        response["id"] = result[0].device_key
        response["name"] = result[0].name

        statement = "SELECT * FROM device_fields WHERE device_id=:device_id\
                ORDER BY field_index ASC"
        result = await self.query(statement, {
                "device_id" : result[0].id
            })

        response["fields"] = list()
        for I in result:
            response["fields"].append({
                    "type" : I.field_type,
                    "name" : I.field_name
                })

        return response

    async def update_device( self, user_id, structure ):
        pass

    async def delete_device_with_id( self, user_id, device_id ):
        pass

    async def delete_device_with_name( self, user_id, device_name ):
        pass

class RestDeviceHandler(RestBaseHandler):
    async def get(self):
        user_id = self.authenticate()

        limit = self.parse_int_argument('limit', 100, 0, 1000)
        page = self.parse_int_argument('page', 0, 0, 0)
        ascending = self.parse_bool_argument('ascending', False)

        devices = await self.get_devices_from_user(user_id,
                                                   limit,
                                                   page,
                                                   ascending)

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(devices))

    async def post(self):
        user_id = self.authenticate()
        
        if not self.request.headers["Content-Type"] == 'application/json':
            raise tornado.web.HTTPError(400)

        args = tornado.escape.json_decode(self.request.body)

        if not args["name"]:
            raise tornado.web.HTTPError(400)
        if not args["fields"]:
            raise tornado.web.HTTPError(400)
        if len(args["fields"]) == 0:
            raise HTTPError(400)

        device = await self.create_new_device(user_id, args)

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(device))

class RestDeviceSingleHandler(RestBaseHandler):
    async def get(self, category, identification):
        user_id = self.authenticate()

        self.validate_string(identification)
        device_id = identification
        device = None
        if category == 'id':
            device = await self.get_device_with_id( user_id, device_id )
        elif category == 'name':
            device = await self.get_device_with_name( user_id, device_id )

        self.set_header("Content-Type", "application/json");

        self.write(json.dumps(device))

    async def patch(self, category, identification):
        user_id = self.authenticate()

        if not self.request.headers["Content-Type"] == 'application/json':
            raise tornado.web.HTTPError(400)

        args = tornado.escape.json_decode(self.request.body)

        self.validate_string(identification)
        device_id = identification
        device = None
        if category == 'id':
            device = await self.get_device_with_id( user_id, device_id )
        elif category == 'name':
            device = await self.get_device_with_name( user_id, device_id )

        if device == None:
            raise tornado.web.HTTPError(404)

        if args["name"]:
            device["name"] = args["name"]
        if args["fields"]:
            device["fields"] = args["fields"]

        await self.update_device( user_id, device )

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(device))

    async def delete(self, category, identification):
        user_id = self.authenticate()

        self.validate_string(identification)
        device_id = identification
        device = None
        if category == 'id':
            device = await self.delete_device_with_id( user_id, device_id )
        elif category == 'name':
            device = await self.delete_device_with_name( user_id, device_id )

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(device))

class RestDataHandler(RestBaseHandler):
    async def get(self):
        user_id = self.authenticate()

        limit = self.parse_int_argument('limit', 100, 0, 1000)
        page = self.parse_int_argument('page', 0, 0, 0)
        ascending = self.parse_bool_argument('ascending', False)

        samples = await self.get_samples_from_user( user_id,
                                                    limit,
                                                    page,
                                                    ascending )

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(samples))

class RestDataSingleHandler(RestBaseHandler):
    async def get(self):
        pass

    async def delete(self):
        pass

class RestDataSingleFieldHandler(RestBaseHandler):
    async def get(self):
        pass

    async def patch(self):
        pass

def handlers():
    return [
        (r"/api/device", RestDeviceHandler),
        (r"/api/device/by_(id|name)/(.*?)", RestDeviceSingleHandler),
        (r"/api/data", RestDataHandler),
        (r"/api/data/by_(id|name)/(.*?)", RestDataSingleHandler),
        (r"/api/data/by_(id|name)/(.*?)/field", RestDataSingleFieldHandler)
    ]
