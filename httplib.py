import socket
import threading
import logging


def recvall(sock):
    fragments = []
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        fragments.append(chunk)
    return b''.join(fragments)


def make_http_response(headers, body, status=200):
    status_info = {
        400: 'Bad Request',
        200: 'OK',
        404: 'Not Found',
        403: 'Forbidden',
        501: 'Not Implemented',
    }
    response_line = f"HTTP/1.0 {status} {status_info[status]}"
    blank_line = ''
    return '\r\n'.join([response_line, *headers, blank_line, body])


def make_http_request(request_type, endpoint, headers, body):
    response_line = f"{request_type} {endpoint} HTTP/1.0"
    blank_line = ''
    return '\r\n'.join([response_line, *headers, blank_line, body])


def parse_raw_response(data):
    data = data.decode("utf-8")
    lines = data.split("\r\n")
    first_line = lines[0].split(" ")
    header_len = 0
    for headerLine in lines[1:]:
        header_len += 1
        if len(headerLine) == 0:
            break
    headers = lines[1:header_len]
    body = '\r\n'.join(lines[header_len + 1:])
    return first_line, headers, body


def parse_http_response(data):
    response_line, headers, body = parse_raw_response(data)
    request = {
        "status": int(response_line[1]),
        "status_info": response_line[2],
        "version": response_line[0],
        "headers": headers,
        "body": body
    }
    return request


def parse_http_request(data):
    request_line, headers, body = parse_raw_response(data)
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
        s.bind((self.host, int(self.port)))
        s.listen(5)
        try:
            logging.info(f"Server Listening for connections at {s.getsockname()}")
            while True:
                conn, addr = s.accept()
                logging.info(f"New Connection by {addr}")
                # Create a thread everytime there's a new request
                threading.Thread(target=self.handle_request, args=(conn, addr)).start()

        finally:
            s.close()

    def handle_request(self, conn, data):
        data = conn.recv(4096)
        logging.debug(f'(request)  {data}')
        try:
            if len(data) == 0:
                raise Exception(400, "Bad Request")
            request = parse_http_request(data)  # Get a parsed HTTP request
            # Invoke get or post handler based on the request type
            request_handler = getattr(self, 'handle_%s' % request["method"])
            response = request_handler(request)
            logging.debug(f'(response) {response.encode("utf-8")}')
            conn.sendall(response.encode("utf-8"))
        except Exception as e:
            code,reason = e.args
            response = make_http_response([], reason, code)
            logging.debug(f'(response) {response.encode("utf-8")}')
            conn.sendall(response.encode("utf-8"))
        finally:
            conn.close()

    def handle_GET(self, request):
        # Will be overriden in derived class
        pass

    def handle_POST(self, request):
        # Will be overriden in derived class
        pass
