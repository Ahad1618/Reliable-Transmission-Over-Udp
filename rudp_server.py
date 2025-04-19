import socket
import json
import argparse

class RUDPServer:
    """
    Reliable UDP Server that implements the following:
    - Packet sequencing and ordering
    - Acknowledgment sending
    - Duplicate packet detection
    - Basic error detection via checksum
    """
    
    def __init__(self, host='0.0.0.0', port=5000, buffer_size=1024):
        """Initialize the RUDP server"""
        self.addr = (host, port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(self.addr)
        self.buffer_size = buffer_size
        self.expected_sequence = 0
        self.received_packets = {}  # Store received data indexed by sequence number
    
    def send_ack(self, sequence_number, client_addr):
        """Send acknowledgment for a received packet"""
        ack_packet = {
            'ack': sequence_number
        }
        ack_bytes = json.dumps(ack_packet).encode('utf-8')
        self.socket.sendto(ack_bytes, client_addr)
        print(f"Sent ACK for sequence number: {sequence_number}")
    
    def verify_checksum(self, data, received_checksum):
        """Verify the checksum of received data"""
        calculated_checksum = sum(ord(c) for c in data) % 65536
        return calculated_checksum == received_checksum
    
    def start(self):
        """Start the server and listen for incoming packets"""
        print(f"RUDP Server started on {self.addr[0]}:{self.addr[1]}")
        
        while True:
            try:
                data, client_addr = self.socket.recvfrom(self.buffer_size)
                packet = json.loads(data.decode('utf-8'))
                
                sequence = packet.get('sequence')
                packet_data = packet.get('data')
                checksum = packet.get('checksum')
                
                print(f"Received packet with sequence number: {sequence} from {client_addr}")
                
                # Check if packet is a duplicate
                if sequence < self.expected_sequence:
                    print(f"Duplicate packet detected: {sequence}, expected: {self.expected_sequence}")
                    # Still send ACK for duplicate packets to handle lost ACKs
                    self.send_ack(sequence, client_addr)
                    continue
                
                # Verify checksum
                if not self.verify_checksum(packet_data, checksum):
                    print(f"Checksum verification failed for packet: {sequence}")
                    continue  # Don't send ACK for corrupted packets
                
                # Store packet data in the correct order
                self.received_packets[sequence] = packet_data
                
                # Send acknowledgment
                self.send_ack(sequence, client_addr)
                
                # Process in-order packets
                self.process_in_order_packets()
                
            except Exception as e:
                print(f"Error: {e}")
    
    def process_in_order_packets(self):
        """Process packets that have arrived in order"""
        while self.expected_sequence in self.received_packets:
            data = self.received_packets[self.expected_sequence]
            print(f"Processing in-order packet {self.expected_sequence}: {data}")
            # In a real application, you would do something with the data here
            
            # Remove the processed packet and increment expected sequence
            del self.received_packets[self.expected_sequence]
            self.expected_sequence += 1
    
    def close(self):
        """Close the socket connection"""
        self.socket.close()

def main():
    parser = argparse.ArgumentParser(description='RUDP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    args = parser.parse_args()
    
    server = RUDPServer(args.host, args.port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    main() 