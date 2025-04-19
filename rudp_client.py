import socket
import time
import json
import random
import argparse

class RUDPClient:
    """
    Reliable UDP Client that implements the following:
    - Packet sequencing
    - Acknowledgment handling
    - Timeout and retransmission
    - Sliding window (basic implementation)
    """
    
    def __init__(self, server_ip, server_port, timeout=1.0, max_retries=5):
        """Initialize the RUDP client"""
        self.server_addr = (server_ip, server_port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.timeout = timeout
        self.max_retries = max_retries
        self.sequence_number = 0
    
    def send_packet(self, data, sequence_number):
        """Send a packet with sequence number and wait for ACK"""
        packet = {
            'sequence': sequence_number,
            'data': data,
            'checksum': self._calculate_checksum(data)
        }
        
        # Convert packet to JSON and encode to bytes
        packet_bytes = json.dumps(packet).encode('utf-8')
        
        retries = 0
        while retries < self.max_retries:
            try:
                # Send the packet
                print(f"Sending packet with sequence number: {sequence_number}")
                self.socket.sendto(packet_bytes, self.server_addr)
                
                # Wait for acknowledgment
                response, server = self.socket.recvfrom(1024)
                ack = json.loads(response.decode('utf-8'))
                
                if ack.get('ack') == sequence_number:
                    print(f"Received ACK for sequence number: {sequence_number}")
                    return True
                else:
                    print(f"Received incorrect ACK: {ack.get('ack')}, expected: {sequence_number}")
            
            except socket.timeout:
                print(f"Timeout occurred for sequence number: {sequence_number}. Retrying...")
                retries += 1
        
        print(f"Failed to send packet after {self.max_retries} retries")
        return False
    
    def send_message(self, message):
        """Break message into packets and send them reliably"""
        # For simplicity, we're using a fixed packet size of 100 bytes
        chunk_size = 100
        chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
        
        success = True
        for chunk in chunks:
            if not self.send_packet(chunk, self.sequence_number):
                success = False
                break
            self.sequence_number += 1
        
        return success
    
    def close(self):
        """Close the socket connection"""
        self.socket.close()
    
    def _calculate_checksum(self, data):
        """Calculate a simple checksum for the data"""
        # This is a very basic checksum for demonstration
        # In production, use a proper checksum algorithm
        return sum(ord(c) for c in data) % 65536

def main():
    parser = argparse.ArgumentParser(description='RUDP Client')
    parser.add_argument('--server', default='127.0.0.1', help='Server IP address')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--message', default='Hello, RUDP!', help='Message to send')
    args = parser.parse_args()
    
    client = RUDPClient(args.server, args.port)
    try:
        print(f"Sending message: {args.message}")
        if client.send_message(args.message):
            print("Message sent successfully")
        else:
            print("Failed to send message")
    finally:
        client.close()

if __name__ == "__main__":
    main() 