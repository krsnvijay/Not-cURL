import argparse
import ipaddress
import socket
from utils import split_data_into_packets, send
from packet import Packet
from packet import Packet, SYN_ACK, SYN, NAK, ACK, FIN


def establish_handshake(server_addr, server_port, router_addr = "127.0.0.1", router_port=3000):
    established = False
    while not established:
        peer_ip = ipaddress.ip_address(socket.gethostbyname(server_addr))
        conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        peer = peer_ip, server_port
        router = router_addr, router_port
        timeout = 10
        try:
            print("trying handshake. Send SYN")
            p = Packet(packet_type=SYN,
                       seq_num=0,
                       peer_ip_addr=peer_ip,
                       peer_port=server_port,
                       payload="Hi S".encode("utf-8"))
            conn.sendto(p.to_bytes(), (router_addr, router_port))
            print('Send "{}" to router'.format("Hi S"))
            # with open("starwars.txt") as f:
            #     file_data = f.read()
            #     send(conn, peer, router, file_data)
            #     return
            #
            # msg = "Hello World"
            # p = Packet(packet_type=0,
            #            seq_num=1,
            #            peer_ip_addr=peer_ip,
            #            peer_port=server_port,
            #            payload=msg.encode("utf-8"))
            # conn.sendto(p.to_bytes(), (router_addr, router_port))
            # print('Send "{}" to router'.format(msg))
            #
            # Try to receive a response within timeout
            conn.settimeout(timeout)
            print('Waiting for a response')
            response, sender = conn.recvfrom(1024)
            p = Packet.from_bytes(response)
            if p.packet_type == SYN_ACK:
                print('Received syn ack, sending ack and data received is {}'.format(p.payload.decode("utf-8")))
                established = True
                p_ack = Packet(packet_type=ACK,
                               seq_num=0,
                               peer_ip_addr=peer_ip,
                               peer_port=server_port,
                               payload="".encode("utf-8"))
                conn.sendto(p_ack.to_bytes(), (router_addr, router_port))
                print("Handshake Done!")
            # print('Router: ', sender)
            # print('Packet: ', p)
            # print('Payload: ' + p.payload.decode("utf-8"))

        except socket.timeout:
            print('No response after {}s'.format(timeout))
        finally:
            return conn, router


# Usage:
# python echoclient.py --routerhost localhost --routerport 3000 --serverhost localhost --serverport 8007




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--routerhost", help="router host", default="localhost")
    parser.add_argument("--routerport", help="router port", type=int, default=3000)

    parser.add_argument("--serverhost", help="server host", default="localhost")
    parser.add_argument("--serverport", help="server port", type=int, default=8008)
    args = parser.parse_args()
    establish_handshake(args.routerhost, args.routerport, args.serverhost, args.serverport)
