import db
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.websocket
import tornado.options
import json

import re

database = db.database(db.database_file)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        items = database.get_samples(100)
        print(len(items[0]))
        self.render("template.html", title="Websockets test", dates=items[0],
                voltage=items[1], current=items[2])

class ArduinoHandler(tornado.websocket.WebSocketHandler):
    channels = set()

    def initialize(self):
        self.ID = 0

    def open(self):
        self.channels.add(self)

    def on_message(self, message):
        server = tornado.ioloop.IOLoop.current()
        channel = None
        for I in self.channels:
            if self == I:
                channel = I
        if channel == None:
            print("Error websocket not found")
            return None

        if self.ID == 0:
            print("Send name " + message)
            self.ID = database.get_device_id(message)
            print("ID retrieved " + str(self.ID))
            print("ID type " + str(type(self.ID)))
        else:
            pattern = "v=\[(.*?)\];c=\[(.*?)\]"
            matches = re.search(pattern, message)
            voltage_list = matches.group(1).split(",")
            current_list = matches.group(2).split(",")
            voltages = [ float(x) for x in voltage_list ]
            currents = [ float(x) for x in current_list ]
            voltages.reverse()
            currents.reverse()
            for i in range(0, len(voltages)):
                database.write_sample( currents[i], voltages[i], self.ID)
            server.add_callback(ClientHandler.send_message, len(voltages))

    def on_close(self):
        self.channels.remove(self)

    def check_origin(self, origin):
        return True

class ClientHandler(tornado.websocket.WebSocketHandler):
    channels = set()

    def initialize(self):
        pass

    def open(self):
        print("Client openened")
        self.channels.add(self)

    def on_message(self, message):
        pass

    def on_close(self):
        self.channels.remove(self)

    @classmethod
    def send_message(cls, message):
        removable = set()
        data = database.get_samples(message)
        obj = dict()
        obj["date"] = data[0]
        obj["voltage"] = data[1]
        obj["current"] = data[2]
        print(len(obj["date"]))

        for ws in cls.channels:
            if not ws.ws_connection or not ws.ws_connection.stream.socket:
                removable.add(ws)
            else:
                ws.write_message(json.dumps(obj))
        for ws in removable:
            cls.channels.remove(ws)

    def check_origin(self, origin):
        return True

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler), 
        (r"/Client", ClientHandler),
        (r"/Arduino", ArduinoHandler)
        ])

if __name__ == "__main__" :
    app = make_app()
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()
