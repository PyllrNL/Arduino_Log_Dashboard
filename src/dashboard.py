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

        user_id = int(self.get_secure_cookie("arduino_dashboard"))
        statement = "SELECT (key) FROM api_keys\
                WHERE user_id=:user_id"
        api_key = await self.query(statement, {"user_id" : user_id})
        self.render("home.html", api_key=api_key[0].key)

class AboutHandler(base.BaseHandler):
    def get(self):
        if not self.get_secure_cookie("arduino_dashboard"):
            self.redirect("/auth/login")
        else:
            self.render("about.html",title="Arduino DashBoard")

class Application(tornado.web.Application):
    def __init__(self, db):
        self.db = db
        handlers = [
            (r"/", HomeHandler),
            (r"/about", AboutHandler),
        ]
        handlers.extend(authHandler.handlers())
        handlers.extend(websocketHandler.handlers())

        settings = dict(
                title=u"Arduino Dashboard",
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                xsrf_cookies=True,
                cookie_secret=cookie_secret.secret,
                login_url="/auth/login",
                debug=True,
        )
        super().__init__(handlers, **settings)

async def main():
    async with aiosqlite.connect("dashboard.db") as db:
        await maybe_create_tables(db)
        app = Application(db)
        app.listen(8080)

        shutdown_event = tornado.locks.Event()
        await shutdown_event.wait()

if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
