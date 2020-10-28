import socket
import argparse

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

parser.add_argument("-v",help="Prints debugging messages.", action="store_true")
parser.add_argument("-p","--port", default=8008,help="Specifies the port number that the server will listen and serve at. Default is 8080.")
parser.add_argument("-d","--directory", default="/",help="Specifies the directory that the server will use to read/write requested files. Default is the current directory when launching the application.")

args = parser.parse_args()