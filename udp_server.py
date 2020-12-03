import argparse
import socket

from packet import Packet, SYN_ACK, SYN, NAK, ACK, FIN
from utils import make_ack, receive

established = False
TIMEOUT = 5


def run_server(port):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        conn.bind(('', port))
        print('Echo server is listening at', port)
        while True:
            data, sender = conn.recvfrom(1024)
            establish_handshake_server(conn, data, sender)

    finally:
        conn.close()


def establish_handshake_server(conn, data, sender):
    global established
    try:
        p = Packet.from_bytes(data)
        peer_ip_addr, peer_port = p.peer_ip_addr, p.peer_port
        # print("Router: ", sender)
        # print("Packet: ", p)
        print("Payload: ", p.payload.decode("utf-8"))
        if not established:
            if p.packet_type == SYN:
                print("Handshake start SYN ")
                p_synack = Packet(SYN_ACK, 0, peer_ip_addr, peer_port, "Hi R".encode("utf-8"))
                conn.sendto(p_synack.to_bytes(), sender)
                print("sending syn_ack")
            elif p.packet_type == ACK:
                print("ACK!!")
                established = True
        # else:
        #         #     p_ack = Packet(ACK, 0, peer_ip_addr, peer_port, p.payload)
        #         #     conn.sendto(p_ack.to_bytes(), sender)
        #         #     print("Handshake done.")
        # request = receive(conn, sender, data)
        # How to send a reply.
        # The peer address of the packet p is the address of the client already.
        # We will send the same payload of p. Thus we can re-use either `data` or `p`.
        # conn.sendto(p.to_bytes(), sender)

    except Exception as e:
        print("Error: ", e)

    finally:
        return conn


def handshake(p, conn, sender):
    peer_ip_addr, peer_port = p.peer_ip_addr, p.peer_port
    if p.packet_type == SYN:
        print("Handshake start SYN ")
        p_synack = Packet(SYN_ACK, 0, peer_ip_addr, peer_port, p.payload)
        conn.sendto(p_synack.to_bytes(), sender)
        print("sending syn_ack")
    elif p.packet_type == SYN_ACK:
        print("ACK!!")
        established = True


# Usage python udp_server.py [--port port-number]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", help="echo server port", type=int, default=8008)
    args = parser.parse_args()
    run_server(args.port)