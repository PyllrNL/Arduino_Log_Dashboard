import base

import bcrypt
import re

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web

import secrets

import time
import calendar

from base import NoResultError

class AuthBaseHandler(tornado.web.RequestHandler):
    def row_to_obj(self, row, cur):
        obj = tornado.util.ObjectDict()
        for val, desc in zip(row, cur.description):
            obj[desc[0]] = val
        return obj

    async def query(self, stmt, kwargs):
        async with (await self.application.db.cursor()) as cur:
            await cur.execute(stmt, kwargs)
            return [self.row_to_obj(row, cur) for row in await cur.fetchall()]

    async def does_user_exist(self, user):
        statement = "SELECT * FROM users WHERE username=:user"
        result = await self.query(statement, {"user":user})
        if len(result) == 0:
            return False
        else:
            return True

    async def does_any_user_exist(self):
        statement = "SELECT * FROM users"
        result = await self.query(statement)
        if len(result) > 0:
            return True
        return False

    async def create_user(self, new_user, hashed_password):
        statement = "INSERT INTO users (username, hashed_password)\
                VALUES (:name, :hashed_password) RETURNING id"
        user = await self.query(statement,
                {"name":new_user,
                 "hashed_password":hashed_password})
        await self.application.db.commit()
        return user[0]

    async def get_user(self, user):
        statement = "SELECT * FROM users WHERE username=:user"
        user_id = await self.query(statement, {"user":user})
        if len(user_id) == 0:
            raise NoResultError
        return user_id[0]

    async def is_login_key_valid(self, key):
        statement = "SELECT * FROM login_keys WHERE key=:key"
        results = await self.query(statement, {"key":key})
        if len(results) == 0:
            return False
        else:
            statement = "DELETE FROM login_keys WHERE key=:key"
            await self.query(statement, {"key":key})
            await self.application.db.commit()
            ts = calendar.timegm(time.gmtime())
            if ts <= results[0].timestamp:
                return True
        return False

class AuthCreateHandler(AuthBaseHandler):
    def get(self):
        self.render("create_author.html", title="Arduino Dashboard")

    async def post(self):
        key = self.get_argument("key")
        if not await self.is_login_key_valid(key):
            raise tornado.web.HTTPError(400, "key is invalid")

        new_user = self.get_argument("username")
        if await self.does_user_exist(new_user):
            raise tornado.web.HTTPError(400, "User already exists")

        hashed_password = await tornado.ioloop.IOLoop.current().run_in_executor(
                None,
                bcrypt.hashpw,
                tornado.escape.utf8(self.get_argument("password")),
                bcrypt.gensalt(),
        )

        user = await self.create_user(new_user, hashed_password)
        new_hash = secrets.token_urlsafe(32).decode("utf-8")
        self.application.user_sessions[new_hash] = user_id

        self.set_secure_cookie(self.application.cookie_name, new_hash)
        self.redirect(self.get_argument("next","/"))

class AuthLoginHandler(AuthBaseHandler):
    async def get(self):
        self.render("login.html", error=None)

    async def post(self):
        try:
            user = await self.get_user(self.get_argument("username"))
        except base.NoResultError:
            self.render("login.html", error="username not found")
            return
        password_equal = await tornado.ioloop.IOLoop.current().run_in_executor(
                None,
                bcrypt.checkpw,
                tornado.escape.utf8(self.get_argument("password")),
                tornado.escape.utf8(user.hashed_password),
        )
        if password_equal:
            new_hash = secrets.token_urlsafe(32)

            for (key,vals) in self.application.user_sessions:
                if vals == user.id:
                    self.application.user_sessions.remove(key)

            self.application.user_sessions[new_hash] = user.id
            print(self.application.user_sessions)

            self.set_secure_cookie(self.application.cookie_name, new_hash)
            self.redirect(self.get_argument("next", "/"))
        else:
            self.render("login.html", error="incorrect_password")

class AuthLogoutHandler(AuthBaseHandler):
    def get(self):
        self.clear_cookie(self.application.cookie_name)
        self.redirect(self.get_argument("next", "/"))

def handlers():
    return [
        (r"/auth/create", AuthCreateHandler),
        (r"/auth/login", AuthLoginHandler),
        (r"/auth/logout", AuthLogoutHandler),
    ]
