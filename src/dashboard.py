import aiosqlite
import bcrypt
import re
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web

import os.path
import cookie_secret

import base
import authHandler
import websocketHandler
import restHandler

from tornado.options import define, options

async def maybe_create_tables(db):
    tables_created = False
    async with (await db.cursor()) as cur:
        statement = "PRAGMA foreign_keys = ON"
        await cur.execute(statement)
        statement = "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
        await cur.execute(statement)
        result = await cur.fetchone()
        if result[0] > 0:
            tables_created = True
    if not tables_created:
        with open("schema.sql", "r") as f:
            schema = f.read()
            async with (await db.cursor()) as cur:
                await cur.executescript(schema)

class HomeHandler(base.BaseHandler):
    async def get(self):
        if self.redirect_if_not_authenticated("/auth/login"):
            return
        self.render("home.html")

class ConfigHandler(base.BaseHandler):
    async def get(self):
        if self.redirect_if_not_authenticated("/auth/login"):
            return
        self.render("config.html")

class AboutHandler(base.BaseHandler):
    def get(self):
        if not self.get_secure_cookie("arduino_dashboard"):
            self.redirect("/auth/login")
        else:
            self.render("about.html",title="Arduino DashBoard")

class Application(tornado.web.Application):
    def __init__(self, db):
        self.db = db
        self.cookie_name = "arduino_dashboard"
        self.user_sessions = dict()
        handlers = [
            (r"/", HomeHandler),
            (r"/about", AboutHandler),
            (r"/config", ConfigHandler),
        ]
        handlers.extend(authHandler.handlers())
        handlers.extend(websocketHandler.handlers())
        handlers.extend(restHandler.handlers())

        settings = dict(
                title=u"Arduino Dashboard",
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                cookie_secret=cookie_secret.secret,
                login_url="/auth/login",
                debug=True,
        )
        super().__init__(handlers, **settings)

async def main():
    async with aiosqlite.connect("dashboard.db") as db:
        await maybe_create_tables(db)
        app = Application(db)
        app.listen(8338)

        shutdown_event = tornado.locks.Event()
        await shutdown_event.wait()

if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
