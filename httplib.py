import ipaddress
import socket
import sys
import threading
import logging

from packet import Packet, ACK, FIN
from udp_server import establish_handshake_server
from utils import make_ack, split_data_into_packets


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


class BaseUDPServer:
    def __init__(self, host='127.0.0.1', port=8080, debug=False):
        self.host = host
        self.port = port
        self.debug = debug

    def run_server(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.bind((self.host, int(self.port)))
        # conn.listen(5)
        try:
            logging.info(f"Server Listening for connections at {conn.getsockname()}")
            while True:
                data, sender = conn.recvfrom(1024)
                logging.info(f"New Connection by {sender}")
                # Create a thread everytime there's a new request
                threading.Thread(target=self.handle_request, args=(conn, data, sender)).start()

        finally:
            conn.close()

    def handle_request(self, conn, data, sender):

        conn = establish_handshake_server(conn, data, sender)
        print(conn)
        peer = (ipaddress.ip_address(self.host), self.port)
        if conn is None:
            print("Handshake failed!")
            sys.exit(0)
        logging.debug(f'(request)  {data}')

        payload = []
        while True:
            raw_data, sender = conn.recvfrom(1024)
            data_packet = Packet.from_bytes(raw_data)
            peer = data_packet.peer_ip_addr, data_packet.peer_port
            print("Packet: ", data_packet)
            print("Payload: ", data_packet.payload.decode("utf-8"))
            ack = make_ack(ACK, data_packet.seq_num, peer)
            print("sender type ", sender, type(sender[0]))
            conn.sendto(ack.to_bytes(), sender)
            print("Ack: ", ack)
            if data_packet.packet_type == FIN:
                print("LastPacket: ", ack)
                break
            else:
                payload.append(data_packet.payload.decode("utf-8"))
        data = ''.join(payload)
        print("data ",data)
        try:
            if len(data) == 0:
                response = make_http_response([],'Bad Request', 400)
            else:
                request = parse_http_request(data)  # Get a parsed HTTP request
                # Invoke get or post handler based on the request type
                request_handler = getattr(self, 'handle_%s' % request["method"])
                response = request_handler(request)
            logging.debug(f'(response) {response.encode("utf-8")}')
            packets = split_data_into_packets(response, peer)
            for packet in packets:
                conn.sendto(packet.to_bytes(), sender)
            fin = make_ack(FIN, len(packets) + 1, peer)
            conn.sendto(fin.to_bytes(), sender)

            while True:
                received_data, sender = conn.recvfrom(1024)
                p = Packet.from_bytes(received_data)
                if p.packet_type == ACK:
                    continue
                break

        except Exception as e:
            print(e)
        finally:
            conn.close()

    def handle_GET(self, request):
        # Will be overriden in derived class
        pass

    def handle_POST(self, request):
        # Will be overriden in derived class
        pass
