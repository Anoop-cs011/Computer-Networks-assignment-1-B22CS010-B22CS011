import socket
import threading
import csv
import pandas as pd

# Global file lock for thread-safe file operations
file_lock = threading.Lock()

class SeedNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.peer_list = []  # List of tuples: (IP, port, degree)
        self.lock = threading.Lock()

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.ip, self.port))
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.listen(500)
        print(f"Seed node started at {self.ip}:{self.port}")

        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        data = client_socket.recv(10240).decode()
        if data.startswith("REGISTER"):
            # Register a new peer
            _, peer_ip, peer_port = data.split(':')
            self.register_peer(peer_ip, int(peer_port))
            client_socket.send(str(self.peer_list).encode())
            # client_socket.send("ACK".encode())
        elif data.startswith("GET_PEERS"):
            # Send the list of peers to the requesting peer
            client_socket.send(str(self.peer_list).encode())
        elif data.startswith("DEAD_NODE"):
            # Remove a dead peer from the list
            _, dead_ip, dead_port, _, _ = data.split(':')
            self.remove_dead_node(dead_ip, int(dead_port))
            # client_socket.send("ACK".encode())
        elif data.startswith("UPDATE_DEGREE"):
            # Update the degree of a peer
            _, peer_ip, peer_port = data.split(':')
            self.update_peer_degree(peer_ip, int(peer_port))
            # client_socket.send("ACK".encode())
        client_socket.close()

    def register_peer(self, peer_ip, peer_port):
        with self.lock:
            # Check if the peer is already registered
            for i, (ip, port, degree) in enumerate(self.peer_list):
                if ip == peer_ip and port == peer_port:
                    return  # Peer is already registered

            # Register the new peer with degree 0
            self.peer_list.append((peer_ip, peer_port, 0))
            print(f"Peer registered: {peer_ip}:{peer_port}")
            with file_lock:
                file1 = open("outputSeed.txt", "a")  # append mode
                file1.write(f"Peer registered: {peer_ip}:{peer_port}\n")
                file1.close()
            # print(f"Registered peer: {peer_ip}:{peer_port}")
            self.write_peer_list_to_csv()

    def remove_dead_node(self, dead_ip, dead_port):
        with self.lock:
            # Remove the dead peer from the list
            self.peer_list = [(ip, port, degree) for (ip, port, degree) in self.peer_list if ip != dead_ip or port != dead_port]
            print(f"Removed dead node: {dead_ip}:{dead_port}")
            self.remove_peer_from_csv(dead_ip, dead_port)

    def update_peer_degree(self, peer_ip, peer_port):
        with self.lock:
            # Update the degree of the specified peer
            for i, (ip, port, degree) in enumerate(self.peer_list):
                if ip == peer_ip and port == peer_port:
                    self.peer_list[i] = (ip, port, degree + 1)
                    # print(f"Updated degree of {peer_ip}:{peer_port} to {degree + 1}")
                    self.write_peer_list_to_csv()
                    break
    
    def write_peer_list_to_csv(self):
        filename = "peer_list.csv"
        with file_lock:  # Ensure thread-safe file access
            try:
                df = pd.read_csv(filename)  # Read existing file
            except FileNotFoundError:
                df = pd.DataFrame(columns=["IP", "Port", "Degree"])  # Create if not exists

            # Convert peer_list to DataFrame
            new_data = pd.DataFrame(self.peer_list, columns=["IP", "Port", "Degree"])

            # Ensure correct data types
            new_data["Port"] = new_data["Port"].astype(int)
            new_data["Degree"] = new_data["Degree"].astype(int)

            # Merge old and new data, keeping the latest values
            df = pd.concat([df, new_data]).drop_duplicates(subset=["IP", "Port"], keep="last")

            # Write updated data back to the file
            df.to_csv(filename, index=False)
    
    def remove_peer_from_csv(self, dead_ip, dead_port):
        filename = "peer_list.csv"
        with file_lock:  # Ensure thread-safe file access
            try:
                df = pd.read_csv(filename)  # Read the existing CSV
            except FileNotFoundError:
                print("Peer list file not found.")
                return

            # Ensure correct data types
            df["Port"] = df["Port"].astype(int)

            # Remove the specific dead peer
            df = df[~((df["IP"] == dead_ip) & (df["Port"] == dead_port))]

            # Write the updated peer list back to the file
            df.to_csv(filename, index=False)
            print(f"Removed dead peer from CSV: {dead_ip}:{dead_port}")
            with file_lock:
                file1 = open("outputSeed.txt", "a")  # append mode
                file1.write(f"Removed dead peer from CSV: {dead_ip}:{dead_port}\n")
                file1.close()

import sys

# if __name__ == "__main__":
#     if len(sys.argv) != 3:
#         print("Usage: python seed.py <IP> <PORT>")
#         sys.exit(1)

#     ip = sys.argv[1]
#     port = int(sys.argv[2])
#     seed = SeedNode(ip, port)
#     seed.start()

if __name__ == "__main__":
    seeds = []
    with open('config.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            ip, port = row
            seeds.append(SeedNode(ip, int(port)))

    for seed in seeds:
        threading.Thread(target=seed.start).start()
