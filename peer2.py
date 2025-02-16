import socket
import threading
import csv
import time
import random

class PeerNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.seeds = set()
        self.peers = set()
        self.message_list = set()  # Use a set to track unique messages
        self.deadPeerCounter = {}
        self.lock = threading.Lock()

    def start(self):
        print(f"Starting peer node at {self.ip}:{self.port}")
        self.load_seeds()
        self.register_with_seeds()
        self.connect_to_peers()
        threading.Thread(target=self.generate_messages).start()
        threading.Thread(target=self.check_liveness).start()
        self.listen_for_messages()

    def load_seeds(self):
        # print("Loading seed nodes from config file...")
        with open('config.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                self.seeds.add((row[0], int(row[1])))
        # print(f"Loaded seeds: {self.seeds}")

    def register_with_seeds(self):
        # print("Registering with seed nodes...")
        n = len(self.seeds)
        k = (n // 2) + 1
        selected_seeds = random.sample(sorted(self.seeds), k)
        for seed_ip, seed_port in selected_seeds:
            self.register_with_seed(seed_ip, seed_port)
        # print("Registration with seed nodes complete.")

    def register_with_seed(self, seed_ip, seed_port):
        # print(f"Registering with seed node at {seed_ip}:{seed_port}...")
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((seed_ip, seed_port))
            client_socket.send(f"REGISTER:{self.ip}:{self.port}".encode())
            response = client_socket.recv(10240).decode()
            # print(f"Received response from seed: {response}")
            response = eval(response)
            # print(type(response))
            if isinstance(response, list):
                response.remove((self.ip, self.port, 0))
                self.peers.update(response)
            
            client_socket.close()
        except Exception as e:
            print(f"Failed to register with seed node {seed_ip}:{seed_port}: {e}")
            # time.sleep(30)
            # self.register_with_seed(seed_ip, seed_port)
    
    def select_peers_with_power_law(self, peer_list, num_peers_to_select):
        """
        Select peers to connect to based on a power-law distribution (preferential attachment).
        :param peer_list: List of peers (IP, port, degree).
        :param num_peers_to_select: Number of peers to select.
        :return: List of selected peers.
        """
        # Calculate the total degree of all peers
        
        # Perform weighted random selection
        selected_peers = set()
        for _ in range(num_peers_to_select):
            total_degree = sum(peer[2] for peer in peer_list)
            # Generate a random number between 0 and total_degree
            rand = random.uniform(0, total_degree)
            cumulative_weight = 0
            for peer in peer_list:
                cumulative_weight += peer[2]  # Add the degree of the peer
                if rand <= cumulative_weight:
                    selected_peers.add(peer)
                    peer_list.remove(peer)
                    break
        print(f"Recieved peer nodes: {selected_peers}")
        return selected_peers

    def connect_to_peers(self):
        # # Fetch the list of peers from seed nodes
        # for seed_ip, seed_port in self.seeds:
        #     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     client_socket.connect((seed_ip, seed_port))
        #     client_socket.send("GET_PEERS".encode())
        #     data = client_socket.recv(1024).decode()
        #     self.peers.extend(eval(data))  # Assume peers are in the format (IP, port, degree)
        #     client_socket.close()

        # Select peers based on power-law distribution
        num_peers_to_select = min(len(self.peers), 5)  # Adjust as needed
        selected_peers = self.select_peers_with_power_law(list(self.peers), num_peers_to_select)
        self.peers = selected_peers
        # Update the degree count of selected peers
        # self.update_peer_degrees_self()
        self.update_peer_degrees_seeds()

        # # Connect to the selected peers
        # for peer_ip, peer_port, _ in selected_peers:
        #     self.send_message(peer_ip, peer_port, "CONNECT")

    def update_peer_degrees_self(self):
        updatedPeers = set()
        for i, (peer_ip, peer_port, deg) in enumerate(self.peers):
                updatedPeers.add((peer_ip, peer_port, deg+1))
        self.peers = updatedPeers

    def update_peer_degrees_seeds(self):
        for peer_ip, peer_port, deg in self.peers:
            for seed_ip, seed_port in self.seeds:
                self.update_peer_degree(seed_ip, seed_port, peer_ip, peer_port)

    def update_peer_degree(self, seed_ip, seed_port, peer_ip, peer_port):
        # print(f"Sending update to seed node at {seed_ip}:{seed_port}...")
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((seed_ip, seed_port))
            client_socket.send(f"UPDATE_DEGREE:{peer_ip}:{peer_port}".encode())
            client_socket.close()
        except Exception as e:
            print(f"Failed to send update to seed node {seed_ip}:{seed_port}: {e}")
            # time.sleep(30)
            # self.update_peer_degree(seed_ip, seed_port, peer_ip, peer_port)
            
    def generate_messages(self):
        # print("Starting message generation...")
        msg_count = 0
        while msg_count < 10:
            time.sleep(5)
            msg = f"{time.time()}:{self.ip}:{self.port}:{msg_count}"
            # print(f"Generated message: {msg}")
            self.broadcast_message(msg)
            msg_count += 1
        # print("Message generation complete.")

    def broadcast_message(self, msg):
        with self.lock:
            if msg not in self.message_list:
                self.message_list.add(msg)  # Add message to the set
                # print(f"Broadcasting message: {msg}")
                for peer_ip, peer_port, _ in self.peers:
                    self.send_message(peer_ip, peer_port, msg)

    def send_message(self, peer_ip, peer_port, msg):
        try:
            # print(f"Sending message to {peer_ip}:{peer_port}: {msg}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((peer_ip, peer_port))
            client_socket.send(msg.encode())
            client_socket.close()
        except Exception as e:
            print(f"Failed to send message to {peer_ip}:{peer_port}: {e}")
            # time.sleep(30)
            # send_message(peer_ip, peer_port, msg)

    def listen_for_messages(self):
        # print(f"Listening for messages at {self.ip}:{self.port}...")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.ip, self.port))
        server_socket.listen(500)

        while True:
            try:
                client_socket, addr = server_socket.accept()
                # print(f"Received connection from {addr}")
                threading.Thread(target=self.handle_message, args=(client_socket,)).start()
            except Exception as e:
                print(f"Error accepting connection: {e}")

    def handle_message(self, client_socket):
        try:
            data = client_socket.recv(10240).decode()
            # print(f"Received data: {data}")

            if data == "PING":
                # Handle ping message
                # print(f"Received PING from {client_socket.getpeername()}")
                client_socket.send("PONG".encode())  # Respond to the ping
            elif data != "ACK":
                # Handle gossip message
                with self.lock:
                    if data not in self.message_list:
                        print(f"Received gossip message: {data}")
                        self.message_list.add(data)  # Add message to the set
                        # print(f"Broadcasting received message: {data}")
                        self.broadcast_message(data)

            client_socket.close()
        except Exception as e:
            print(f"Error handling message: {e}")

    def check_liveness(self):
        # print("Starting liveness check...")
        failure_count = {}  # Dictionary to track consecutive ping failures

        while True:
            time.sleep(13)
            dead_peers = []
            
            for peer_ip, peer_port, deg in self.peers:
                if not self.ping_peer(peer_ip, peer_port):
                    failure_count[(peer_ip, peer_port)] = failure_count.get((peer_ip, peer_port), 0) + 1
                    # print(f"Ping failed for {peer_ip}:{peer_port}. Failure count: {failure_count[(peer_ip, peer_port)]}")
                    
                    if failure_count[(peer_ip, peer_port)] >= 3:  # Mark as dead after 3 failures
                        dead_peers.append((peer_ip, peer_port, deg))
                else:
                    failure_count[(peer_ip, peer_port)] = 0  # Reset failure count if ping succeeds

            for dead_ip, dead_port, deg in dead_peers:
                self.report_dead_node(dead_ip, dead_port)
                self.peers.remove((dead_ip, dead_port, deg))
                del failure_count[(dead_ip, dead_port)]  # Remove from failure tracking

            # print(f"Liveness check complete. Dead peers: {dead_peers}")

    def ping_peer(self, peer_ip, peer_port):
        try:
            # print(f"Pinging {peer_ip}:{peer_port}...")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((peer_ip, peer_port))
            client_socket.send("PING".encode())
            response = client_socket.recv(10240).decode()
            client_socket.close()
            if response == "PONG":
                # print(f"Ping successful for {peer_ip}:{peer_port}")
                return True
            else:
                print(f"Unexpected response from {peer_ip}:{peer_port}: {response}")
                return False
        except Exception as e:
            print(f"Ping failed for {peer_ip}:{peer_port}: {e}")
            return False

    def report_dead_node(self, dead_ip, dead_port):
        # print(f"Reporting dead node {dead_ip}:{dead_port}...")
        for seed_ip, seed_port in self.seeds:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((seed_ip, seed_port))
                client_socket.send(f"DEAD_NODE:{dead_ip}:{dead_port}:{time.time()}:{self.ip}".encode())
                client_socket.recv(10240)
                client_socket.close()
            except Exception as e:
                print(f"Failed to report dead node to seed {seed_ip}:{seed_port}: {e}")

import sys

# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Usage: python peer.py <IP> <PORT>")
#         sys.exit(1)

#     ip = sys.argv[1]
#     port = int(sys.argv[2])
#     peer = PeerNode(ip, port)
#     peer.start()

if __name__ == "__main__":
    peers = []
    with open('peers.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            ip, port = row
            peers.append(PeerNode(ip, int(port)))

    for peer in peers:
        threading.Thread(target=peer.start).start()
        # time.sleep(1)