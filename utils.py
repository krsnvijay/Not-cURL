from packet import Packet, SYN_ACK, SYN, ACK, NAK, DATA, FIN

TIMEOUT = 5


def split_data_into_packets(data, peer, seq = 0, packet_type=DATA, payload_size=1013):
    peer_ip_addr, peer_port = peer
    packets = []
    # split data based on packet size
    # create packet
    while seq * payload_size < len(data):
        payload = data[seq * payload_size: (seq + 1) * payload_size]
        p = Packet(packet_type, seq + 1, peer_ip_addr, peer_port, payload.encode("utf-8"))
        packets.append(p)
        seq += 1
    return packets


def combine_packets_into_data(packets):
    data = []
    # extract payload of each packet
    for packet in packets:
        data.append(packet.payload.decode("utf-8"))
    return ''.join(data)


def make_ack(packet_type, seq_num, peer, payload=''):
    peer_ip_addr, peer_port = peer
    return Packet(packet_type, seq_num, peer_ip_addr, peer_port, payload.encode("utf-8"))


def establish_connection(conn, peer, router):
    # syn = make_ack(0, peer, "Hi S")
    syn = make_ack(SYN, 0, peer, "Hi S")
    conn.sendto(syn.to_bytes(), router)
    received_data, sender = conn.recvfrom(1024)
    received_packet = Packet.from_bytes(received_data)
    established = False
    if received_packet.packet_type == SYN_ACK:
        pack_ack = make_ack(ACK, 0, peer, "")
        conn.sendto(pack_ack.to_bytes(), router)
        established = True
    return established


def send(conn, peer, router, data):
    # 3 way handshake
    if establish_connection(conn, peer, router):
        packets = split_data_into_packets(data, peer)
        for packet in packets:
            conn.sendto(packet.to_bytes(), router)
        fin = make_ack(FIN, len(packets) + 1, peer, 'eof')
        conn.sendto(fin.to_bytes(), router)

    while True:
        received_data, sender = conn.recvfrom(1024)
        p = Packet.from_bytes(received_data)
        if p.packet_type == ACK:
            continue
        break


def receive(conn, router, data):
    p = Packet.from_bytes(data)
    print("Router: ", router)
    print("Packet type: ", p.packet_type)
    print("Payload: ", p.payload.decode("utf-8"))
    peer = p.peer_ip_addr, p.peer_port
    if p.packet_type == SYN:
        packet_syn_ack = make_ack(SYN_ACK, 0, peer, "Hi R")
        conn.sendto(packet_syn_ack.to_bytes(), router)
        payload = []
        while True:
            raw_data, sender = conn.recvfrom(1024)
            data_packet = Packet.from_bytes(raw_data)
            print("Packet: ", data_packet)
            print("Payload: ", data_packet.payload.decode("utf-8"))
            ack = make_ack(ACK, data_packet.seq_num, peer)
            conn.sendto(ack.to_bytes(), sender)
            print("Ack: ", ack)
            if data_packet.packet_type == FIN:
                print("LastPacket: ", ack)
                break
            else:
                payload.append(data_packet.payload.decode("utf-8"))

        return ''.join(payload)