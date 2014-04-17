import tornado
import imp
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
import subprocess
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
    methods = {}
    def get(self):
        self.write("You're not doing it right")

    def post(self):
        print(self.request)
        self.filepath=self.request.files['img'][0]['filename']
        self.set_secure_cookie('file', self.filepath)
        fileinfo = self.request.files['img'][0]
        print("Java file recieved: "+str(fileinfo))
        fname = fileinfo['filename']
        with open(self.filepath, 'w') as f:
            f.write(str(fileinfo['body'])) #For some reason, quotation marks are included. Strip them.
        try:
            subprocess.check_call(['javac',self.filepath])
        except Exception as e:
            self.write("Code did not compile")
            print(e)
            return
        try:
            analyze=subprocess.check_output(['java', 'ClassInfoAnalyzer', self.filepath[:-5]]).decode()
            print("Analyze:", analyze )
            print("Analyze(Sliced):", str( analyze[:-1] ))
            #eval('self.method='+str(analyze))
            self.methods = {}
            [self.methods.update(i) for i in eval(analyze)]
        except Exception as e:
            print(e)
            self.write("Code could not be analyzed")
        print("Methods:", self.methods)
        self.render("java.html",json = json.dumps(self.methods), methods = self.methods, uri = self.request.host)


class PythonHandler(BaseHandler):
    def get(self):
        self.write("Nope, still wrong")

    def post(self):
        self.uid = self.get_secure_cookie('uid').decode()
        print(self.request)
        fileinfo = self.request.files['img'][0]
        print("Python file recieved: "+str(fileinfo))
        fname = fileinfo['filename']
        print(fileinfo['body'])
        with open("tmp/"+self.uid+".py", 'w') as f:
            f.write(str(fileinfo['body'])) #For some reason, quotation marks are included. Strip them.
        clazz = imp.load_module('clazz',*imp.find_module(self.uid, ['tmp/']))
        methods = {i[0]:[i for i in inspect.getargspec(i[1])] for i in inspect.getmembers(clazz) if inspect.isfunction(i[1])} #Maps function names to input lists
        print(methods)
        self.render("python.html", methods = methods, json = json.dumps(methods), uri = self.request.host)

class HomeHandler(BaseHandler):
    def get(self):
        h = hashlib.new('sha1')
        h.update(str(random.randint(-10000, 10000)).encode()) #Generate randomized user id for files
        self.clear_all_cookies()
        self.set_secure_cookie('uid', 'a' + str(h.hexdigest())) #Python files must start with a letter
        self.render("index.html")

class JavaWebsocket(tornado.websocket.WebSocketHandler):

    def open(self):
        self.filename = self.get_secure_cookie('file')
        self.uid = self.get_secure_cookie('uid')

    def unbox_array(self, array):
        acc = ""
        for i in array: acc += str(i)+','
        return acc

    def on_message(self, message):
        print(str(self.uid) + " says " + str(message))
        message = json.loads(message) #Message is in format {"method":{"expected_val":["args"]}}
        for call in list(message):  #method dictionary key
            for case in list(message[call]): #expected return value
                self.write_message(str(subprocess.check_output(['java', 'SuiteGeneratorAPI', str(self.filename[:-5].decode()), str('Test'+call), str(case), str(call), self.unbox_array(message[call][case][:-1])[:-1], 'TestThingy'])))

    def on_close(self):
        print("Goodbye, "+str(self.uid))

class PythonWebSocket(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("uid")
        if not user_id:
            return None
        return user_id

    def open(self):
        self.uid = self.get_secure_cookie('uid')
        print("Python user "+self.uid.decode()+" connected")
        clazz = list(map(__import__, ["tmp."+str(self.uid)[2:-1]])) #Dynamically import relevant file
        self.methods = {i[0]:i[1] for i in inspect.getmembers(clazz[0]) if inspect.isfunction(i[1])} #Maps function names to input lists

    def on_message(self, message):
        print(str(self.uid) + " says " + str(message))
        message = json.loads(message) #Message is in format {"method":{"expected_val":["args"]}}
        for call in list(message):  #method dictionary key
            for case in list(message[call]): #expected return value
                try:
                    print(self.methods[call](*message[call][case]))
                    assert str(self.methods[call](*message[call][case])) == str(case), '{"'+call+'":['+str(case)+','+str(self.methods[call](*message[call][case]))+']}'
                except AssertionError as e:
                    self.write_message(str(e))
                    return
        self.write_message("passed")

    def on_close(self):
        print("Goodbye, "+str(self.uid))

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
