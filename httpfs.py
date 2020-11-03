import socket
import argparse
import pathlib
import threading
import http.server
import socketserver
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
Handler = http.server.SimpleHTTPRequestHandler

print(default_path)

parser.add_argument("-v",help="Prints debugging messages.", action="store_true")
parser.add_argument("-p","--port", default=default_port,help="Specifies the port number that the server will listen and serve at. Default is 8080.")
parser.add_argument("-d","--directory", default=default_path,help="Specifies the directory that the server will use to read/write requested files. Default is the current directory when launching the application.")

args = parser.parse_args()

with socketserver.TCPServer(("",args.port), Handler) as httpd:
    print("Serving at ", Handler)
    httpd.serve_forever()