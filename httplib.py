import ipaddress
import socket
import sys
import threading
import logging

from packet import Packet, ACK, FIN, SYN, SYN_ACK, DATA
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
        self.clients = {}
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run_server(self):
        self.conn.bind((self.host, self.port))
        server = (self.host, self.port)
        try:
            logging.info(f"Server Listening for connections at {self.conn.getsockname()}")
            while True:
                data, router = self.conn.recvfrom(1024)
                packet = Packet.from_bytes(data)
                client = str(packet.peer_ip_addr), packet.peer_port
                if client not in self.clients:
                    # handshake
                    self.handshake_server(client, packet, router, server)
                else:
                    # Create a thread everytime there's a new request
                    threading.Thread(target=self.handle_request, args=(packet, client, router)).start()
        finally:
            self.conn.close()

    def handshake_server(self, client, packet, router, server):
        if packet.packet_type == SYN:
            logging.debug(f'({client}->{server}):{packet}:Reveived SYN')
            # send syn-ack
            syn_ack_pkt = make_ack(SYN_ACK, packet.seq_num, client)
            logging.debug(f'({server}->{client}):{syn_ack_pkt}:Sending SYN-ACK')
            self.conn.sendto(syn_ack_pkt.to_bytes(), router)
        if packet.packet_type == ACK:
            # add sender to connections
            logging.debug(f'({server}->{client}):Received ACK, Connection Established')
            self.clients[client] = {
                "request": {},
                "response": {}
            }

    def handle_request(self, packet, client, router):
        server = (self.host, self.port)
        is_receive_complete = "request_length" in self.clients[client] and self.clients[client][
            "request_length"] == len(
            self.clients[client]["request"])

        if is_receive_complete:
            # if received the full request, send response
            self.send_response(client, packet, router, server)

        else:
            # receive request packets, till FIN
            self.recieve_request(client, packet, router, server)
            is_receive_complete = "request_length" in self.clients[client] and self.clients[client][
                "request_length"] == len(
                self.clients[client]["request"])
            if is_receive_complete:
                # if received the full request, send response
                self.send_response(client, packet, router, server)

    def recieve_request(self, client, packet, router, server):
        # receive packets
        ack_pkt = make_ack(ACK, packet.seq_num, client)
        if packet.packet_type == DATA:
            if packet.seq_num in self.clients[client]["request"]:
                # duplicate seq num detected send ack
                logging.debug(f'({server}->{client}):{ack_pkt}:Duplicate detected, Sending ACK')
            else:
                # add received packet to request dict and send ack
                self.clients[client]["request"][packet.seq_num] = packet
                logging.debug(f'({server}->{client}):{ack_pkt}:Received data packet, Sending ACK')
        if packet.packet_type == FIN:
            # last packet recieved, use seq num to store packets length
            logging.debug(f'({server}->{client}):{ack_pkt}:Received FIN, Sending ACK')
            self.clients[client]["request_length"] = packet.seq_num - 1
        # send ack to client  for the current packet
        self.conn.sendto(ack_pkt.to_bytes(), router)

    def send_response(self, client, packet, router, server):
        if packet.packet_type == ACK:
            # check if all packets have received acks
            self.validate_ack(client, packet, server)
        else:
            # make response into packets and send them

            # combine packets to data
            payload = [self.clients[client]["request"][p].payload for p in
                       sorted(self.clients[client]["request"].keys())]
            raw_request = b''.join(payload)
            logging.debug(f'(request) {raw_request}')

            # make http response
            if len(raw_request) == 0:
                response = make_http_response([], 'Bad Request', 400)
            else:
                request = parse_http_request(raw_request)  # Get a parsed HTTP request
                # Invoke get or post handler based on the request type
                request_handler = getattr(self, 'handle_%s' % request["method"])
                response = request_handler(request)
            logging.debug(f'(response) {response.encode("utf-8")}')

            # send http response
            packets = split_data_into_packets(response, client)
            fin_pkt = make_ack(FIN, len(packets) + 1, client)
            packets.append(fin_pkt)
            for p in packets:
                logging.debug(f'({server}->{client}):{p}:Sending response packet')
                self.conn.sendto(p.to_bytes(), router)
                # store packets in dict, later use that dict for checking acks

                self.clients[client]["response"][p.seq_num] = p

    def validate_ack(self, client, packet, server):
        if packet.seq_num in self.clients[client]["response"]:
            logging.debug(f'({client}->{server}):{packet}:ACK received for response packet')
            # remove a response packet from dict if ack is received
            del self.clients[client]["response"][packet.seq_num]

            # if no packets in response dict, all the packets have been sent
            is_response_complete = len(self.clients[client]["response"]) == 0
            if is_response_complete:
                logging.debug(f'({server}->{client}):Response Finished')
                # close connection
                del self.clients[client]
        else:
            logging.debug(f'({client}->{server}):{packet}: Duplicate ACK received, ignoring it')

    def handle_GET(self, request):
        # Will be overriden in derived class
        pass

    def handle_POST(self, request):
        # Will be overriden in derived class
        pass


class BaseUDPClient:
    def __init__(self, router, host='127.0.0.1', port=8080, debug=False):
        self.host = host
        self.port = port
        self.debug = debug
        self.communication = {
            "response": {},
            "request": {}
        }
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.router = router

    def handshake_client(self):
        established = False
        server = self.host, self.port

        while not established:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            logging.debug("(Starting Handshake)")
            syn_pkt = make_ack(SYN, 0, server)
            logging.debug(f'(client->{server}):{syn_pkt}:Sending SYN')
            self.conn.sendto(syn_pkt.to_bytes(), self.router)
            # TODO timeout

            raw_packet, router = self.conn.recvfrom(1024)
            p = Packet.from_bytes(raw_packet)
            if p.packet_type == SYN_ACK:
                logging.debug(f'({server}->client):{p}:Received SYN_ACK')
                established = True
                ack_pkt = make_ack(ACK, 0, server)
                logging.debug(f'(client->{server}):{p}:Send ACK')
                self.conn.sendto(ack_pkt.to_bytes(), router)
                logging.debug("(Handshake Finished)")
                return established

    def send_request(self, request):
        server = self.host, self.port

        # send request packets
        packets = split_data_into_packets(request, server)
        fin_pkt = make_ack(FIN, len(packets) + 1, server)
        packets.append(fin_pkt)
        for p in packets:
            logging.debug(f'(client->{server}):{p}:Send Request Packet')
            self.conn.sendto(p.to_bytes(), self.router)
            # store packets in dict, later use that dict for checking acks
            self.communication["request"][p.seq_num] = p

        # validate acks for request packets
        while True:
            raw_packet, router = self.conn.recvfrom(1024)
            packet = Packet.from_bytes(raw_packet)
            if packet.seq_num in self.communication["request"]:
                logging.debug(f'({server}->client):{packet}:ACK received')
                # remove a request packet from dict if ack is received
                del self.communication["request"][packet.seq_num]

                # if no packets in response dict, all the packets have been sent
                is_response_complete = len(self.communication["request"]) == 0
                if is_response_complete:
                    logging.debug(f'(client->{server}):Request Finished')
                    # close connection
                    break
            else:
                logging.debug(f'({server}->client):{packet}: Duplicate ACK received, ignoring it')

    def receive_response(self):
        server = self.host, self.port

        # receive packets
        while True:
            is_receive_complete = "response_length" in self.communication and self.communication[
                "response_length"] == len(
                self.communication["response"])

            if is_receive_complete:
                logging.debug(f'(Received Response)')
                break
            raw_packet, sender = self.conn.recvfrom(1024)
            packet = Packet.from_bytes(raw_packet)
            ack_pkt = make_ack(ACK, packet.seq_num, server)
            if packet.packet_type == DATA:
                if packet.seq_num in self.communication["response"]:
                    # duplicate seq num detected send ack
                    logging.debug(f'(client->{server}):{ack_pkt}:Duplicate detected, Sending ACK')
                else:
                    # add received packet to request dict and send ack
                    self.communication["response"][packet.seq_num] = packet
                    logging.debug(f'(client->{server}):{ack_pkt}:Received data packet, Sending ACK')
            if packet.packet_type == FIN:
                # last packet recieved, use seq num to store packets length
                logging.debug(f'(client->{server}):{ack_pkt}:Received FIN, Sending ACK')
                self.communication["response_length"] = packet.seq_num - 1
            # send ack to client  for the current packet
            self.conn.sendto(ack_pkt.to_bytes(), self.router)

        # combine packets to data

        payload = [self.communication["response"][p].payload for p in sorted(self.communication["response"].keys())]
        raw_response = b''.join(payload)
        logging.debug(f'(response) {raw_response}')
        return raw_response
