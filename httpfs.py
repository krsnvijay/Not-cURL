import socket
import threading
import argparse
import pathlib


def run_server(host, port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((host, port))
        listener.listen(5)
        print('File server is listening at', port)
        while True:
            conn, addr = listener.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    finally:
        listener.close()


def handle_client(conn, addr):
    print('New client from', addr)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            data = data.decode("utf-8")
            # TODO, Pos does not actually find start position of body, needs fixing
            pos = data.find('\r\n\r\n')
            lines = data.split("\n")
            method, path, version = lines[0].split(" ")

            path = path.lstrip("/")
            body = ""
            # If path is root, list files
            if path == "":
                currentDirectory = pathlib.Path('.')
                files = [str(f) for f in currentDirectory.iterdir()]
                body = "\n".join(files)

            # Handle path for get request (read if exists)
            elif method == "GET":
                print("Reading from file 📖")
                with open(path, 'r') as f:
                    body = f.read()

            # Handle path for post request (create or overwrite)
            elif method == "POST":
                print("Writing to file")
                with open(path, 'w') as f:
                    f.write(data[pos+4:])
                    body = "Wrote content to file 🖨"

            # Give success/fail response codes
            response = f'''HTTP/1.0 200 OK

{body}'''
            conn.sendall(response.encode("utf-8"))
    finally:
        conn.close()


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

print(default_path)

parser.add_argument("-v", help="Prints debugging messages.",
                    action="store_true")
parser.add_argument("-p", "--port", default=default_port,
                    help="Specifies the port number that the server will listen and serve at. Default is 8080.")
parser.add_argument("-d", "--directory", default=default_path,
                    help="Specifies the directory that the server will use to read/write requested files. Default is the current directory when launching the application.")

args = parser.parse_args()

run_server('', args.port)

# Server
# python httpfs.py
# Client
# list files
# python httpc.py -get "http://localhost"

# read file
# python httpc.py -get "https://localhost/out.txt"

# write file
# python httpc.py -post "https://localhost/nice.txt" -f "datafile.json"
