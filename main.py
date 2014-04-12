import tornado
import json
import random
import hashlib
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
import subprocess
import os.path
import sys
import inspect

from tornado.options import define, options, parse_command_line

define("port", 8080)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        return user_id

class JavaHandler(BaseHandler):
    def get(self):
        self.write("You're not doing it right")

    def post(self):
        self.render("java.html")

class PythonHandler(BaseHandler):
    def get(self):
        self.write("Nope, still wrong")

    def post(self):
        self.render("python.html")

class HomeHandler(BaseHandler):
    def get(self):
        h = hashlib.new('sha1')
        h.update(str(random.randint(-100, 100)).encode())
        self.clear_all_cookies()
        self.set_secure_cookie('uid', str(h.hexdigest()))
        self.write("This will do something interesting. I promise.")

@tornado.web.authenticated
class JavaWebsocket(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        return user_id

    def open(self):
        self.uid = self.get_secure_cookie('uid')

    def on_message(self, message):
        print(str(self.uid) + " says " + str(message))

class PythonWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        self.uid = self.get_secure_cookie('uid')
        clazz = list(map(__import__, ['uploads.' + str(self.uid)[2:-1]])) #Dynamically import relevant file
        self.methods = {i[0]:[j for j in inspect.getargspec(i[1]) if j is not None] for i in inspect.getmembers(clazz[0]) if inspect.isfunction(i[1])} #Maps function names to input lists

    def on_message(self, message):
        print(str(self.uid) + " says " + str(message))
        if message == "hello":
            self.write_message(json.dumps(self.methods))

def main():
    server = tornado.web.Application(
            [
                (r"/", HomeHandler),
                (r"/java", JavaHandler),
                (r"/python", PythonHandler),
                (r"/javafuntime", JavaWebsocket),
                (r"/pythonfuntime", PythonWebSocket)
            ],
            title="LaHacks Server",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            login_url="/",
            cookie_secret="sooper secure, obviously",
            debug=True
        )
    parse_command_line()
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
