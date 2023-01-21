import struct
import socket

# Inspired by https://github.com/barneygale/MCRcon

class RconIncompletePacket(Exception):
    def __init__(self, remaining):
        self.remaining = remaining

class RconPacketTooBig(Exception):
    def __init__(self, length):
        self.length = length

class RconPacketTooSmall(Exception):
    def __init__(self, length):
        self.length = length

class RconWrongPadding(Exception):
    def __init__(self, padding):
        self.padding = padding

class RconPacket():
    def __init__(self, session_id, packet_type, payload):
        self.session_id = session_id
        self.packet_type = packet_type
        self.payload = payload

class RconClient():
    def __init__(self, host, port, password):
        self.session_id = 0
        self.is_connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        print(f'Connecting to {host}:{port}...')
        self.sock.settimeout(10)
        
        try:
            self.sock.connect((host, port))
        except socket.error as e:
            print(f'Connection failed: {e}')
            return

        self.sock.settimeout(None)

        print('Logging in...')
        self.send_packet(RconPacket(self.session_id, 3, password.encode()))
        response = self.receive_packet()
        if response.session_id != self.session_id:
            print('Login failed!')
            return

        print('Connected!')
        self.is_connected = True

    def console(self):
        if not self.is_connected:
            return
        
        print('Type .exit to disconnect from the server')
        while True:
            cmd = input('> ')
            if cmd == '.exit':
                print('Closing connection...')
                self.sock.close()
                self.is_connected = False
                break

            response = self.send_command(cmd)
            print(response)

    def send_command(self, command):
        self.send_packet(RconPacket(self.session_id, 2, command.encode()))
        return self.receive_packet().payload.decode()

    def send_packet(self, packet):
        data = struct.pack('<ii', packet.session_id, packet.packet_type) + packet.payload + b'\0\0'
        self.sock.sendall(struct.pack('<i', len(data)) + data)
    
    def decode_packet(self, data):
        if len(data) < 14:
            raise RconIncompletePacket(14)

        length = struct.unpack('<i', data[:4])[0] + 4

        if length > 4110:
            raise RconPacketTooBig(length)

        if length < 14:
            raise RconPacketTooSmall(length)

        if len(data) < length:
            raise RconIncompletePacket(len(data) - length)

        session_id, packet_type = struct.unpack('<ii', data[4:12])
        payload, padding = data[12:length - 2], data[length - 2:length]

        if padding != b'\0\0':
            raise RconWrongPadding(padding)

        return RconPacket(session_id, packet_type, payload)

    def receive_packet(self):
        data = self.sock.recv(14)
        while True:
            try:
                return self.decode_packet(data)
            except RconIncompletePacket as e:
                data += self.sock.recv(len(data) - e.remaining)
