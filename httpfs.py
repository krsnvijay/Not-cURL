import argparse
import pathlib
import os
import mimetypes
from readerswriterlock import ReadersWriterLock
from httplib import BaseUDPServer, make_http_response, parse_http_request
import logging


# from udp_server import

class SimpleFTPServer(BaseUDPServer):

    def __init__(self, host='127.0.0.1', port=8080, debug=False, directory=None):
        if directory is None:
            directory = os.getcwd()
        self.directory = pathlib.Path(directory)
        logging.info(f"Serving files in {self.directory}")
        super().__init__(host, port, debug)
        self.files = {}

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
            "Content-Disposition: inline",
            "Content-Type: text/plain"
        ]
        response = make_http_response(headers, body, 200)
        return response

    def read_file(self, request):
        headers = []
        file_path = self.directory.joinpath(request["path"])
        if not file_path.exists() or file_path.is_dir():
            headers.append(f"Content-Type: text/plain")
            headers.append("Content-Disposition: inline")
            response = make_http_response(headers, "Requested file doesn't exist", 404)
            return response

        # Only read file if its from the same working directory
        if file_path.resolve().parent != self.directory.resolve():
            headers.append(f"Content-Type: text/plain")
            headers.append("Content-Disposition: inline")
            response = make_http_response(headers, "User doesn't have required permissions", 403)
            return response

        headers.append("Content-Disposition: inline")

        # Guess Content-Type from file extension
        content_type = mimetypes.guess_type(str(file_path.resolve()))
        headers.append(f"Content-Type: {content_type[0]}")
        absolute_file_path = file_path.resolve()
        # Get readwrite lock for a file
        if absolute_file_path not in self.files:
            self.files[absolute_file_path] = ReadersWriterLock()
        with self.files[absolute_file_path].readers_locked():
            with open(file_path, 'r') as f:
                body = f.read()
                response = make_http_response(headers, body, 200)
                return response

    def write_file(self, request):
        headers = [f"Content-Type: text/plain", "Content-Disposition: inline"]
        file_path = self.directory.joinpath(request["path"])
        # Can write only in the working directory
        if file_path.resolve().parent != self.directory.resolve():
            response = make_http_response(headers, "User doesn't have required permissions", 403)
            return response
        absolute_file_path = file_path.resolve()
        # Get readwrite lock for a file
        if absolute_file_path not in self.files:
            self.files[absolute_file_path] = ReadersWriterLock()
        with self.files[absolute_file_path].writer_locked():
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
if __name__ == "__main__":
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
                        help="Specifies the directory that the server will use to read/write requested files. Default is "
                             "the current directory when launching the application.")

    args = parser.parse_args()

    if args.v:
        log_level = "DEBUG"
        fmt = '%(asctime)s %(threadName)s %(message)s'
    else:
        log_level = "INFO"
        fmt = '%(asctime)s %(message)s'
    logging.basicConfig(format=fmt,
                        level=os.environ.get("LOGLEVEL", log_level))
    server = SimpleFTPServer(port=args.port, debug=args.v, directory=args.directory)
    server.run_server()

# Server
# python httpfs.py
# Client
# list files
# python httpc.py -get "http://127.0.0.1:8080/"

# read file
# python httpc.py -get "https://127.0.0.1:8080//out.txt"
# python httpc.py -get "https://127.0.0.1:8080/out.txt"

# write file
# python httpc.py -post "https://127.0.0.1:8080/nice.txt" -f "datafile.json"

# File not found
# python httpc.py -get "http://127.0.0.1:8080/randomfile.json"

# Test path permission - security
# python httpfs.py -v -d "C:\Users\Siddharth\Desktop\Study\University\Fall\Networks\Lab1\Not-cURL\fs"
# python httpc.py -v -get "http://127.0.0.1:8080/../fs/nice.txt"
# python httpc.py -v -get "http://127.0.0.1:8080/nice.json"

# ContentType and Disposition
# python httpc.py -get "http://127.0.0.1:8080/another.json"
# python httpc.py -get "http://127.0.0.1:8080/nice.txt"
# python httpc.py -get "http://127.0.0.1:8080/food.xml"

# concurrency check
# python concurrency_check.py
