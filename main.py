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

# Define the port that the server will be running on
define("port", 8080)

class BaseHandler(tornado.web.RequestHandler):
    """""
    Gets and decodes current userid
    """
    def get_current_user(self):
        user_id = self.get_secure_cookie("uid").decode()
        if not user_id:
            return None
        return user_id

class JavaHandler(BaseHandler):
    """""
    Handles Java section of the website. This handler will take a .java file from
    the user and fill in a template for the user to fill out that will allow for
    unit tests to be generated.
    """
    methods = {}

    # HTTP GET not defined for this handler.
    def get(self):
        self.redirect('/')

    # Post will handle grabbing the file, parsing it, and generating content
    def post(self):
        """""
        Handles an HTTP POST request for this handler. Grabs the file, parses
        it, compiles it, and generates content based on it.
        """
        # Print out the HTTP POST request
        print(self.request)

        # Grab data from the post request
        self.filepath=self.request.files['img'][0]['filename']
        self.set_secure_cookie('file', self.filepath)
        fileinfo = self.request.files['img'][0]

        print("Java file recieved: "+str(fileinfo))
        fname = fileinfo['filename']

        # Write the retrived data from the POST request into a file
        with open(self.filepath, 'w') as f:
            f.write(str(fileinfo['body']))
        try:
            # Attempt to compile the file with the javac compiler
            subprocess.check_call(['javac',self.filepath])
        except Exception as e:
            self.write("Code did not compile")
            print(e)
            return
        try:
            # Analyze the class file using the java tool "ClassInfoAnalyzer"
            class_name = self.filepath[:-5]
            analyze=subprocess.check_output(['java', 'ClassInfoAnalyzer', class_name]).decode()

            print("Analyze:", analyze )
            print("Analyze(Sliced):", str( analyze[:-1] ))

            # Parse the data generated
            self.methods = {}
            [self.methods.update(i) for i in eval(analyze)]
        except Exception as e:
            print(e)
            self.write("Code could not be analyzed")

        # Render HTML content
        print("Methods:", self.methods)
        self.render("java.html",json = json.dumps(self.methods),
                methods = self.methods, uri = self.request.host)


class PythonHandler(BaseHandler):
    """""
    This class will handle HTTP GET and HTTP POST requests that are passed by
    clients to the server.
    """
    def get(self):
        """""
        This handler does not handle HTTP GET requests
        """
        self.redirect('/')

    def post(self):
        # Read the data from the POST request
        self.uid = self.get_current_user()
        fileinfo = self.request.files['img'][0]
        fname = fileinfo['filename']

        # Write file to procedurally generated file
        with open("tmp/" + self.uid + ".py", 'w') as f:
            f.write( fileinfo['body'].decode() )

        # Dynamically load the user's python file
        clazz = imp.load_module('clazz', *imp.find_module(self.uid, ['tmp/']))

        # Map methods to their arguments
        methods = {}
        for member in inspect.getmembers(clazz):
            member_name = member[0]
            member_body = member[1]
            if inspect.isfunction( member_body ):
                args = inspect.getargspec( member_body )#[0]
                methods.update( {member_name : args} )

        # Print out data from the POST request
        print("Python file recieved: "+str(fileinfo))
        print(fileinfo['body'])
        print(methods)

        # Generate the HTML fields using the python template
        self.render("python.html", methods = methods,
                json = json.dumps(methods), uri = self.request.host)

class HomeHandler(BaseHandler):
    """""
    This class will handle how the server handles connections made to the home
    page for the server (index.html).
    """
    def get(self):
        #Generate randomized user id for files
        h = hashlib.new('sha1')
        h.update(str(random.randint(-10000, 10000)).encode())

        self.clear_all_cookies()

        #Python files must start with a letter
        self.set_secure_cookie('uid', 'a' + str(h.hexdigest()))
        self.render("index.html")

class JavaWebsocket(tornado.websocket.WebSocketHandler):
    """""
    This class will handle the .java files being uploaded for testing to the
    application.
    """
    def open(self):
        """""
        Gathers data when the socket connection is opened
        """
        self.filename = self.get_secure_cookie('file')
        self.uid = self.get_secure_cookie('uid')

    def unbox_array(self, array):
        """""
        Splits the passed array into a comma separated list.
        """
        acc = ""
        for i in array: acc += str(i)+','
        return acc

    def on_message(self, message):
        """""
        Executes java tests using the passed values
        """
        print(str(self.uid) + " says " + str(message))
        message = json.loads(message) #Message is in format {"method":{"expected_val":["args"]}}
        for call in list(message):  #method dictionary key
            for case in list(message[call]): #expected return value
                self.write_message(str(subprocess.check_output(['java', 'SuiteGeneratorAPI', str(self.filename[:-5].decode()), str('Test'+call), str(case), str(call), self.unbox_array(message[call][case][:-1])[:-1], call+"Tests"])))

    def on_close(self):
        """""
        Prints a message to the terminal when a user exists, along with their
        user id.
        """
        print("Goodbye, "+str(self.uid))

class PythonWebSocket(tornado.websocket.WebSocketHandler):
    """""
    Handles the websocket interface for the python section of the website. This
    will use the information entered by the user and generate the test cases
    based on the information entered into the HTML forms.
    """
    def get_current_user(self):
        """""
        Stores a unique cookie for each user as their user id.
        """
        user_id = self.get_secure_cookie("uid").decode()
        if not user_id:
            return None
        return user_id

    def open(self):
        """""
        Opens and analyzes the python file that was uploaded by the user
        """
        # Retrieve the user ID cookie
        self.uid = self.get_current_user()

        # Dynamically import the uploaded file to access its members
        clazz = imp.load_module( 'clazz', *imp.find_module(self.uid, ['tmp/']) )

        # Map modules method names to its methods
        methods = {}
        for member in inspect.getmembers( clazz ):
            member_name = member[0]
            member_body = member[1]
            if inspect.isfunction( member_body ):
                methods.update( {member_name : member_body } )
        self.methods = methods

    def on_message(self, message):
        """""
        Handles the messages sent by the user. These messages will be the
        methods and expected return values for those methods. This information
        will be parsed and the expected values will be asserted agains the actual
        return values from the functions.
        """
        # Print out the message sent by the user
        print(str(self.uid) + " says " + str(message))

        # Parse the JSON message sent by the user.
        # Message will be formatted as: {"method":{"expected":["args"]}}
        #   E.G: {"factorial":{"120":[5]}} would be equivalent to "assert factorial(5) == 120"
        message = json.loads(message)
        errors = {}
        for call in list(message):  #method dictionary key
            for case in list(message[call]): #expected return value

                    # Test the actual result of the function against the expected
                    result = str( self.methods[call](*message[call][case]) )

                    # Print out the result
                    print(result)

                    # If the results doesn't equal the expected results, add a message to errors
                    # NOTE: As is, this only allows for one test per method
                    if not result == str(case):
                        errors.update({call:[str(case), result]})

        # Package all test results into a single message
        self.write_message(json.dumps(errors))

    def on_close(self):
        """""
        When a user closes their connection with the server, print out a message
        to terminal with their user id.
        """
        print("Goodbye, "+str(self.uid))

def main():
    """""
    Start up the server and register the necessary handlers and web socket
    interfaces.
    """
    # Register the handlers and web socket interfaces
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

    # Starts the tornado server
    parse_command_line()
    server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
