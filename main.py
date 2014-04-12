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
        print(self.request.files)
        fileinfo = self.request.files['img'][0]
        print("Python file recieved: "+str(fileinfo))
        fname = fileinfo['filename']
        with open(str(self.get_secure_cookie('uid'))[2:-1]+'.py', 'w') as f:
            f.writelines([i+'\n' for i in str(fileinfo['body']).split('\\n')])
        clazz = list(map(__import__, [str(self.get_secure_cookie('uid'))[2:-1]])) #Dynamically import relevant file
        methods = {i[0]:[i for i in inspect.getargspec(i[1])] for i in inspect.getmembers(clazz[0]) if inspect.isfunction(i[1])} #Maps function names to input lists
        print(methods)
        self.render("python.html", methods = methods, json = json.dumps(methods))

class HomeHandler(BaseHandler):
    def get(self):
        h = hashlib.new('sha1')
        h.update(str(random.randint(-10000, 10000)).encode())
        self.clear_all_cookies()
        self.set_secure_cookie('uid', 'a' + str(h.hexdigest()))
        self.render("index.html")

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
    def get_current_user(self):
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        return user_id

    def open(self):
        self.uid = self.get_secure_cookie('uid')
        clazz = list(map(__import__, [str(self.uid)[2:-1]])) #Dynamically import relevant file
        self.methods = {i[0]:i[1] for i in inspect.getmembers(clazz[0]) if inspect.isfunction(i[1])} #Maps function names to input lists

    def on_message(self, message):
        print(str(self.uid) + " says " + str(message))
        message = json.loads(message)
        for call in list(message):  #method dictionary key
            for case in list(message[call]): #expected return type
                try:
                    assert str(self.methods[call](*message[call][case])) == str(case), "expected "+str(case)+", got "+str(self.methods[call](*message[call][case]))
                except AssertionError as e:
                    self.write_message(str(e))
                    return
        self.write_message("passed")

def main():
    server = tornado.web.Application(
            [
                (r"/", HomeHandler),
                (r"/java/", JavaHandler),
                (r"/python/", PythonHandler),
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
