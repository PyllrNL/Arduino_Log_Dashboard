import aiosqlite
import re

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web

class NoResultError(Exception):
    pass

class BaseHandler(tornado.web.RequestHandler):
    def redirect_if_not_authenticated(self, redirection):
        if not self.get_secure_cookie("arduino_dashboard"):
            self.redirect(redirection)
            return True
        return False

    def row_to_obj(self, row, cur):
        obj = tornado.util.ObjectDict()
        for val, desc in zip(row, cur.description):
            obj[desc[0]] = val
        return obj

    async def query(self, stmt, options):
        async with (await self.application.db.cursor()) as cur:
            await cur.execute(stmt, options)
            return [self.row_to_obj(row, cur) for row in await cur.fetchall()]

    async def queryone(self, stmt, options):
        result = await self.query(stmt, options)
        if len(result) == 0:
            raise NoResultError
        else:
            return result[0]

    async def querycount(self, stmt, options):
        result = await self.query(stmt, options)
        return result[0]['COUNT(*)']

    async def query_vertical(self, stmt, options):
        async with (await self.application.db.cursor()) as cur:
            await cur.execute(stmt, options)
            raw = await cur.fetchall()
            data = dict()
            data["0"] = [ x[0] for x in raw ]
            data["1"] = [ x[1] for x in raw ]
            data["2"] = [ x[2] for x in raw ]
            return data

    async def does_user_exists(self, user):
        statement = "SELECT * FROM users WHERE username=:user"
        result = await self.query(statement, {"user": user})
        if len(result)==0:
            print("returning false")
            return False
        else:
            return True

    async def create_user(self, new_user, hashed_password):
        statement = "INSERT INTO users (username, hashed_password)\
                VALUES (:name, :hashed_password) RETURNING id"
        user = await self.query(statement, {"name":new_user, "hashed_password":hashed_password})
        await self.application.db.commit()
        return user

    async def get_user(self, user):
        statement = "SELECT * FROM users WHERE username=:user"
        user_id = await self.query(statement, {"user":user})
        return user_id
