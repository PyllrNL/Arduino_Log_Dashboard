import tornado.ioloop
import tornado.httpserver
import tornado.web
import base
import json
import secrets
import msgpack
from io import StringIO
import csv
import datetime

class RestBaseHandler(base.BaseHandler):
    def authenticate(self):
        user_key = self.get_secure_cookie(self.application.cookie_name).decode("utf-8")
        if user_key == None:
            raise tornado.web.HTTPError(403)
        if user_key not in self.application.user_sessions:
            self.redirect("/auth/login")
        return self.application.user_sessions[user_key]

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
                (:user_id, :name, :device_key)"

        await self.query(statement, {
                "user_id" : user_id,
                "name" : structure["name"],
                "device_key" : device_key
            })

        statement = "SELECT * FROM devices WHERE user_id=:user_id\
                ORDER BY id DESC LIMIT 1"

        result = await self.query(statement, {"user_id":user_id})

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

    async def delete_device_with_id( self, user_id, device_id ):
        print("Function to delete device");
        response = dict()

        statement = "SELECT * FROM devices WHERE device_key=:device_key"
        result = await self.query(statement, {"device_key" : device_id})

        response["id"] = result[0].device_key
        response["name"] = result[0].name

        device_num = result[0].id

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

        statement = "DELETE FROM device_fields WHERE device_id=:device_id"
        await self.query(statement, {"device_id" : device_num })

        print(device_num)
        statement = "SELECT COUNT(*) FROM samples WHERE device_id=:device_id"
        rows_left = await self.query(statement, {"device_id" : device_num })
        while rows_left != 0:
            statement = "DELETE FROM samples WHERE id in (\
                    SELECT id FROM samples WHERE device_id=:device_id LIMIT 10000"
            await self.query(statement, {"device_id" : device_num })
            if rows_left > 10000:
                rows_left = rows_left - 10000
            else:
                rows_left = 0

        print("Deleting this device", device_id)
        statement = "DELETE FROM devices WHERE device_key=:device_key"
        await self.query(statement, {"device_key" : device_id})
        await self.application.db.commit()

        return response

    async def delete_device_with_name( self, user_id, device_name ):
        response = dict()

        statement = "SELECT * FROM devices WHERE name=:name"
        result = await self.query(statement, {"name" : device_name})

        response["id"] = result[0].device_key
        response["name"] = result[0].name

        device_id = result[0].id

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

        statement = "DELETE FROM device_fields WHERE device_id=:device_id"
        await self.query(statement, {"device_id" : device_id })

        statement = "DELETE FROM devices WHERE device_key=:device_key"
        await self.query(statement, {"device_key" : response["id"]})
        await self.application.db.commit()

        return response

    async def get_samples( self, device_id, limit, page, ascending ):
        response = dict()

        statement = "SELECT * from devices where device_key=:device_key"
        result = await self.query(statement, {"device_key": device_id})
        device = result[0]

        print(device_id)
        statement = "SELECT COUNT(*) from samples where device_id=:device_id"
        result = await self.querycount(statement, {"device_id": device.id})

        div = int(result / limit)
        response["total_pages"] = div if div > 0 else 1
        response["page"] = page
        response["data"] = dict()

        if result == 0:
            return response

        retrieve_limit = limit * (page + 1)

        statement = "SELECT * from samples where device_id=:device_id ORDER BY\
                id {} LIMIT {}".format(
                        "ASC" if ascending else "DESC",
                        retrieve_limit)
        
        result = await self.query(statement, {
                "device_id" : device.id,
            })

        statement = "SELECT * from device_fields where device_id=:device_id"
        device_fields = await self.query(statement, {"device_id" : device.id})

        response["data"]["timestamp"] = list()
        value_index = list()
        for I in device_fields:
            response["data"][I.field_name] = list()
            value_index.insert(I.field_index, I.field_name)

        for I in range(limit * page, len(result)):
            response["data"]["timestamp"].append(result[I].timestamp)
            data = msgpack.unpackb( result[I].data )
            for J in range(0, len(data)):
                response["data"][value_index[J]].append(data[J])

        return response

    async def get_dashboards_with_user(self, user_id):
        response = list()

        statement = "SELECT * FROM dashboards WHERE user_id=:user_id"
        result = await self.query(statement, {"user_id": user_id})

        for I in result:
            single_result = dict()
            single_result["id"] = I.id
            single_result["samples"] = I.samples
            single_result["fields"] = list()

            statement = "SELECT * FROM dashboard_fields WHERE dashboard_id\
                    =:dashboard_id"
            fields = await self.query( statement, {"dashboard_id" : I.id })
            for J in fields:
                statement = "SELECT * FROM device_fields WHERE id=:id"
                dev_fields = await self.query( statement, {"id" : J.device_fields_id})
                dev_fields = dev_fields[0]
                statement = "SELECT * FROM devices WHERE id=:id"
                device = await self.query( statement, {"id" : dev_fields.device_id})
                device = device[0]
                single_result["fields"].append({
                        "device_name" : device.name,
                        "id" : device.device_key,
                        "name" : dev_fields.field_name
                    })
            response.append(single_result)
        return response

    async def create_new_dashboard( self, user_id, args ):
        response = dict()

        device_fields = list()
        for I in args["fields"]:
            device = None
            if "device_name" in I.keys():
                statement = "SELECT * from devices WHERE name=:name"
                device = await self.query(statement, {"name": I["device_name"]})
            elif "device_id" in I.keys():
                statement = "SELECT * from devices WHERE device_key=:device_key"
                device = await self.query(statement, {"device_key": I["device_id"]})
            statement = "SELECT * from device_fields WHERE device_id=:device_id\
                    AND field_name=:name"
            field = await self.query(statement, {
                    "device_id" : device[0].id,
                    "name" : I["name"]
                })
            device_fields.append((device[0], field[0]))

        statement = "INSERT INTO dashboards (user_id, samples) VALUES\
                (:user_id, :samples)"
        await self.query(statement, {
                "user_id" : user_id,
                "samples" : args["samples"]
            })

        statement = "SELECT * FROM dashboards WHERE user_id=:user_id\
                ORDER BY id DESC LIMIT 1"

        dashboard = await self.query(statement, {"user_id":user_id})

        dashboard = dashboard[0]

        statement = "INSERT INTO dashboard_fields (dashboard_id, device_fields_id)\
                VALUES (:dash_id, :field_id)"

        for I in device_fields:
            await self.query(statement, {
                    "dash_id" : dashboard.id,
                    "field_id" : I[1].id
                })

        response["id"] = dashboard.id
        response["samples"] = args["samples"]
        response["fields"] = list()
        for I in device_fields:
            single_result = dict()
            single_result["name"] = I[1].field_name
            single_result["id"] = I[0].device_key
            response["fields"].append(single_result)

        await self.application.db.commit()

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(response))

    async def get_single_dashboard( self, dashboard_id ):
        response = dict()

        statement = "SELECT * FROM dashboards WHERE id=:id"
        dashboard = await self.query(statement, {"id": dashboard_id})
        dashboard = dashboard[0]

        response["id"] = dashboard.id
        response["samples"] = dashboard.samples
        response["fields"] = list()

        statement = "SELECT * FROM dashboard_fields WHERE dashboard_id\
                =:id"
        fields = await self.query(statement, {"id" : dashboard.id})
        for I in fields:
            statement = "SELECT * FROM device_fields WHERE id=:id"
            dev_field = await self.query(statement, {"id": I.device_fields_id})
            dev_field = dev_field[0]
            statement = "SELECT * FROM devices WHERE id=:id"
            device = await self.query(statement, {"id" : dev_field.device_id})
            device = device[0]
            single_result = dict()
            single_result["name"] = dev_field.field_name
            single_result["id"] = device.device_key
            response["fields"].append(single_result)

        return response

    async def delete_single_dashboard( self, dashboard_id ):
        response = await self.get_single_dashboard( dashboard_id )

        statement = "DELETE FROM dashboard_fields WHERE dashboard_id=:id"
        await self.query(statement, {"id": dashboard_id})

        statement = "DELETE FROM dashboards WHERE id=:id"
        await self.query(statement, {"id": dashboard_id})

        await self.application.db.commit()

        return response


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

    async def delete(self, category, identification):
        user_id = self.authenticate()

        self.validate_string(identification)
        device_id = identification
        device = None
        if category == 'id':
            print("Deleting device");
            device = await self.delete_device_with_id( user_id, device_id )
        elif category == 'name':
            device = await self.delete_device_with_name( user_id, device_id )

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(device))

class RestDataSingleHandler(RestBaseHandler):
    async def get(self, category, identification):
        user_id = self.authenticate()

        limit = self.parse_int_argument('limit', 100, 0, 10000)
        page = self.parse_int_argument('page', 0, 0, 0)
        ascending = self.parse_bool_argument('ascending', False)

        self.validate_string(identification)
        device_id = identification
        device = None
        if category == 'id':
            device = await self.get_device_with_id( user_id, device_id )
        elif category == 'name':
            device = await self.get_device_with_name( user_id, device_id )

        self.set_header("Content-Type", "application/json")

        if device == None:
            raise tornado.web.HTTPError(404)

        samples = await self.get_samples( device["id"],
                                          limit,
                                          page,
                                          ascending )

        self.write(json.dumps(samples))


class RestDataSingleFieldHandler(RestBaseHandler):
    async def get(self, category, identification):
        user_id = self.authenticate()

        limit = self.parse_int_argument('limit', 100, 0, 100000)
        page = self.parse_int_argument('page', 0, 0, 0)
        ascending = self.parse_bool_argument('ascending', False)

        fields = self.get_arguments('field')

        self.validating_string(identification)
        device_id = identification
        device = None
        if category == 'id':
            device = await self.get_device_with_id( user_id, device_id )
        elif category == 'name':
            device = await self.get_device_with_name( user_id, device_id )

        self.set_header("Content-Type", "application/json")

        if device == None:
            raise tornado.web.HTTPError(404)

        samples = await self.get_samples( device["id"],
                                          limit,
                                          page,
                                          ascending )

        response = dict()
        response["total_pages"] = samples["total_pages"]
        response["page"] = samples["page"]

        response["data"] = dict()
        for I in fields:
            if samples["data"][I]:
                response["data"][I] = samples["data"][I]

        return response

class RestDashboardHandler(RestBaseHandler):
    async def get(self):
        user_id = self.authenticate()

        dashboards = await self.get_dashboards_with_user( user_id )

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(dashboards))

    async def post(self):
        user_id = self.authenticate()
        
        if not self.request.headers["Content-Type"] == 'application/json':
            raise tornado.web.HTTPError(400)

        print(self.request.body)
        args = tornado.escape.json_decode(self.request.body)

        if not args["samples"]:
            raise tornado.web.HTTPError(400)
        if not args["fields"]:
            raise tornado.web.HTTPError(400)
        if len(args["fields"]) == 0:
            raise HTTPError(400)

        dashboard = await self.create_new_dashboard(user_id, args)

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(dashboard))

class RestDashboardSingleHandler(RestBaseHandler):
    async def get(self, dashboard_id):
        user_id = self.authenticate()

        dashboard = await self.get_single_dashboard( dashboard_id )

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(dashboard))

    async def delete(self, dashboard_id):
        user_id = self.authenticate()

        dashboard = await self.delete_single_dashboard( dashboard_id )

        self.set_header("Content-Type", "application/json")

        self.write(json.dumps(dashboard))

class DownloadHandler(RestBaseHandler):
    async def get(self, device_name):
        user_id = self.authenticate()

        statement = "SELECT * FROM devices WHERE name=:device_name"
        device = await self.query(statement, {"device_name": device_name})
        device = device[0]
        self.set_header("Content-Type", "text/csv");
        self.set_header("Content-Disposition", "attachment; filename=" + device_name + ".csv")

        statement = "SELECT * FROM device_fields WHERE device_id=:device_id"
        fields = await self.query(statement, {"device_id" : device["id"]})

        field_list = list()
        for i in fields:
            field_list.insert( i.field_index, i.field_name )

        response = dict()
        response["timestamp"] = list()
        for i in field_list:
            response[i] = list()

        f = StringIO()
        keys = response.keys()
        writer = csv.writer(f, delimiter=",")
        writer.writerow(keys)
        self.write(f.getvalue())

        count, string = self.get_samples(0)
        offset = count
        self.write(string)
        while count == 1000000:
            count, string = self.get_samples(offset)
            offset += count
            self.write(string)

    async def get_samples(self, offset):
        f = StringIO()
        writer = csv.writer(f, delimiter=",")
        statement = "SELECT * FROM samples WHERE device_id=:device_id\
                ORDER BY id DESC LIMIT 1000000 OFFSET :offset"
        data = await self.query(statement, {"device_id" : device["id"],
                                            "offset" : offset})
        for i in data:
            dateobj = datetime.datetime.fromtimestamp( i.timestamp / 1000000000.0).strftime("%Y/%m/%d %H:%M:%S.%f")
            response["timestamp"].append(dateobj)
            info = msgpack.unpackb(i.data)
            for j in range(0, len(info)):
                response[field_list[j]].append(info[j])
        length = len(response["timestamp"])
        writer.writerows(zip(*[response[key] for key in keys]))
        return len(data), f.getvalue()

def handlers():
    return [
        (r"/api/device", RestDeviceHandler),
        (r"/api/device/by_(id|name)/(.*?)", RestDeviceSingleHandler),
        (r"/api/data/by_(id|name)/(.*?)", RestDataSingleHandler),
        #(r"/api/data/by_(id|name)/(.*?)/field", RestDataSingleFieldHandler),
        (r"/api/dashboard", RestDashboardHandler),
        (r"/api/dashboard/(.*?)", RestDashboardSingleHandler),
        (r"/download/device/by_name/(.*?)", DownloadHandler),
    ]
