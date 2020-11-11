import socket
import threading
import argparse
import pathlib
import os
import mimetypes


def make_http_response(headers, body, status=200):
    status_info = {
        200: 'OK',
        404: 'Not Found',
        403: 'Forbidden',
        501: 'Not Implemented',
    }
    response_line = f"HTTP/1.0 {status} {status_info[status]}"
    blank_line = ''
    return '\r\n'.join([response_line, *headers, blank_line, body])


def parse_http_request(data):
    data = data.decode("utf-8")
    lines = data.split("\r\n")
    request_line = lines[0].split(" ")
    header_len = 0
    for headerLine in lines[1:]:
        header_len += 1
        if len(headerLine) == 0:
            break
    headers = lines[1:header_len]
    body = '\r\n'.join(lines[header_len + 1:])
    request = {
        "method": request_line[0],
        "path": request_line[1].lstrip("/"),
        "version": request_line[2],
        "headers": headers,
        "body": body
    }
    return request


class BaseTCPServer:
    def __init__(self, host='127.0.0.1', port=8080, debug=False):
        self.host = host
        self.port = port
        self.debug = debug

    def run_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        try:
            print("Server Listening for connections at", s.getsockname())
            while True:
                conn, addr = s.accept()
                print("New Connection by ", addr)
                threading.Thread(target=self.handle_request, args=(conn, addr)).start()

        finally:
            s.close()

    def handle_request(self, conn, data):
        """Handles incoming data and returns a response.
        Override this in subclass.
        """
        return data


class SimpleFTPServer(BaseTCPServer):

    def __init__(self, host='127.0.0.1', port=8080, debug=False, directory=None):
        if directory is None:
            directory = os.getcwd()
        self.directory = pathlib.Path(directory)
        print("Serving files in", self.directory)
        super().__init__(host, port, debug)

    def handle_request(self, conn, data):
        """Handles incoming requests"""
        data = conn.recv(4096)
        request = parse_http_request(data)  # Get a parsed HTTP request

        request_handler = getattr(self, 'handle_%s' % request["method"])
        response = request_handler(request)
        if self.debug:
            print(data)
            print(request)
            print(response)
        conn.sendall(response.encode("utf-8"))

    def handle_GET(self, request):
        if request["path"] == "":
            return self.list_dir()
        else:
            return self.read_file(request)

    def handle_POST(self, request):
        return self.write_file(request)

    def list_dir(self):
        files = [str(f) for f in self.directory.iterdir()]
        body = "\r\n".join(files)
        headers = [
            "Content-Disposition: inline"
        ]
        response = make_http_response(headers, body, 200)
        return response

    def read_file(self, request):
        headers = []
        file_path = self.directory.joinpath(request["path"])
        if not file_path.exists() or file_path.is_dir():
            response = make_http_response(headers, "Requested file doesn't exist", 404)
            return response

        # Only read file if its from the same working directory
        if file_path.resolve().parent != self.directory.resolve():
            response = make_http_response(headers, "User doesn't have required permissions", 403)
            return response

        headers.append("Content-Disposition: inline")

        # Guess Content-Type from file extension
        content_type = mimetypes.guess_type(file_path.resolve())
        headers.append(f"Content-Type: {content_type[0]}")
        with open(file_path, 'r') as f:
            body = f.read()
            response = make_http_response(headers, body, 200)
            return response

    def write_file(self, request):
        headers = []
        file_path = pathlib.Path(request["path"])
        # Can write only in the working directory
        if file_path.resolve().parent != self.directory.resolve():
            response = make_http_response(headers, "User doesn't have required permissions", 403)
            return response
        with open(file_path, 'w') as f:
            f.write(request["body"])
            response = make_http_response(headers, "Wrote content to file", 200)
            return response


"""
httpfs is a simple file server.
usage: httpfs [-v] [-p PORT] [-d PATH-TO-DIR]

-v  Prints debugging messages.
-p  Specifies the port number that the server will listen and serve at.
    Default is 8080.
-d  Specifies the directory that the server will use to read/write requested files. 
    Default is the current directory when launching the application.
"""

parser = argparse.ArgumentParser(
    description="httpfs is a simple file server.",
    usage='''\n%(prog)s [-v] [-p PORT] [-d PATH-TO-DIR]''',
    prog="httpfs"
)

default_port = 8080
default_path = pathlib.Path().absolute()


parser.add_argument("-v", help="Prints debugging messages.",
                    action="store_true")
parser.add_argument("-p", "--port", default=default_port,
                    help="Specifies the port number that the server will listen and serve at. Default is 8080.")
parser.add_argument("-d", "--directory", default=default_path,
                    help="Specifies the directory that the server will use to read/write requested files. Default is the current directory when launching the application.")

args = parser.parse_args()

if args.v:
    print(args)
server = SimpleFTPServer(port=args.port, debug=args.v, directory=args.directory)
server.run_server()

# Server
# python httpfs.py
# Client
# list files
# python httpc.py -get "http://localhost"

# read file
# python httpc.py -get "https://localhost/out.txt"

# write file
# python httpc.py -post "https://localhost/nice.txt" -f "datafile.json"

# File not found
# python httpc.py -get "http://localhost/randomfile.json"

# Test path permission - security
# python httpfs.py -v -d "C:\Users\Not A Hero\OneDrive\Desktop\6461-1\fs"
# python httpc.py -get "http://localhost/../fs/nice.txt"
# python httpc.py -get "http://localhost/nice.json"

# ContentType and Disposition
# python httpc.py -get "http://localhost/another.json"
# python httpc.py -get "http://localhost/nice.txt"
# python httpc.py -get "http://localhost/food.xml"
