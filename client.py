import socket
import argparse
import sys
import time
import random
from rudp_simulation import RUDPPacket, NetworkSimulator, SimulationVisualizer, print_simulation_header

class RUDPClient:
    """RUDP Client implementation using real sockets"""
    
    def __init__(self, server_host="127.0.0.1", server_port=5000,
                 loss_rate=0.2, corruption_rate=0.1,
                 delay_min=0.05, delay_max=0.2,
                 timeout=1.0, max_retries=3):
        self.server_address = (server_host, server_port)
        
        # Create a UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        
        # Setup network simulator for artificial conditions
        self.network = NetworkSimulator(loss_rate, corruption_rate, delay_min, delay_max)
        self.visualizer = SimulationVisualizer()
        
        # Client state
        self.next_sequence = 0
        self.timeout = timeout
        self.max_retries = max_retries
    
    def send_message(self, message):
        """Send a message reliably using RUDP"""
        self.visualizer.log_info(f"Sending message to {self.server_address[0]}:{self.server_address[1]}")
        
        # First check if server is reachable
        try:
            # Send a quick ping packet to check if server is available
            ping_packet = RUDPPacket(sequence=0, data="PING")
            self.socket.sendto(ping_packet.to_json().encode(), self.server_address)
            self.visualizer.log_info("Checking if server is available...")
            
            try:
                # Wait for a response with a short timeout
                json_data, server_address = self.socket.recvfrom(1024)
                self.visualizer.log_info("Server is reachable, proceeding with message transmission")
            except socket.timeout:
                self.visualizer.log_info("Server did not respond to initial ping. Make sure server is running.")
                return False
            except Exception as e:
                self.visualizer.log_info(f"Error connecting to server: {str(e)}")
                return False
        except Exception as e:
            self.visualizer.log_info(f"Error sending ping to server: {str(e)}")
            return False
        
        # Break message into chunks
        chunk_size = 5  # Small size for demonstration
        chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
        
        start_time = time.time()
        
        for chunk in chunks:
            # Create packet
            packet = RUDPPacket(sequence=self.next_sequence, data=chunk)
            retries = 0
            sent = False
            
            while not sent and retries < self.max_retries:
                try:
                    # Simulate packet loss
                    if self.network.should_drop_packet():
                        self.visualizer.log_sent_packet("CLIENT", packet, is_retransmission=(retries > 0))
                        self.visualizer.log_dropped_packet(packet)
                        retries += 1
                        time.sleep(self.timeout / 2)  # Wait a bit less than the full timeout
                        continue
                    
                    # Simulate network delay
                    delay = self.network.get_delay()
                    time.sleep(delay)
                    
                    # Simulate corruption
                    if self.network.should_corrupt_packet():
                        # Corrupt the packet
                        corrupted_packet = RUDPPacket(sequence=packet.sequence, data=packet.data)
                        corrupted_packet.checksum = random.randint(0, 65535)  # Set invalid checksum
                        self.visualizer.log_sent_packet("CLIENT", corrupted_packet, is_retransmission=(retries > 0))
                        try:
                            self.socket.sendto(corrupted_packet.to_json().encode(), self.server_address)
                        except Exception as e:
                            self.visualizer.log_info(f"Error sending corrupted packet: {str(e)}")
                        retries += 1
                        time.sleep(self.timeout / 2)
                        continue
                    
                    # Log sent packet
                    self.visualizer.log_sent_packet("CLIENT", packet, is_retransmission=(retries > 0))
                    
                    # Send the packet
                    self.socket.sendto(packet.to_json().encode(), self.server_address)
                    
                    # Wait for ACK
                    try:
                        json_data, server_address = self.socket.recvfrom(1024)
                        
                        # Simulate packet loss for ACK (server to client)
                        if self.network.should_drop_packet():
                            ack_packet = RUDPPacket.from_json(json_data.decode())
                            self.visualizer.log_dropped_packet(ack_packet)
                            retries += 1
                            continue
                        
                        # Process the ACK
                        ack_packet = RUDPPacket.from_json(json_data.decode())
                        
                        # Log received ACK
                        self.visualizer.log_received_packet("CLIENT", ack_packet)
                        
                        # Verify this is the ACK we're expecting
                        if ack_packet.is_ack and ack_packet.ack_number == self.next_sequence:
                            self.next_sequence += 1
                            sent = True
                        else:
                            self.visualizer.log_info(f"Unexpected ACK number: {ack_packet.ack_number}, expected: {self.next_sequence}")
                    
                    except socket.timeout:
                        self.visualizer.log_timeout("CLIENT", packet.sequence)
                        retries += 1
                        continue
                    
                except ConnectionResetError:
                    self.visualizer.log_info("Connection was reset by the server. The server might have closed.")
                    retries += 1
                    time.sleep(0.5)  # Wait a bit before retrying
                except Exception as e:
                    self.visualizer.log_info(f"Error during transmission: {str(e)}")
                    retries += 1
            
            if not sent:
                self.visualizer.log_info(f"Failed to send chunk '{chunk}' after {self.max_retries} retries")
                return False
        
        end_time = time.time()
        self.visualizer.log_info(f"Message sent successfully. Total time: {end_time - start_time:.2f} seconds")
        return True
    
    def close(self):
        """Close the socket"""
        self.socket.close()


def main():
    parser = argparse.ArgumentParser(description="RUDP Client")
    parser.add_argument("--server", default="127.0.0.1", help="Server IP address")
    parser.add_argument("--port", type=int, default=5000, help="Server port")
    parser.add_argument("--message", default="Hello, RUDP! This is a test of reliable communication.", help="Message to send")
    parser.add_argument("--loss-rate", type=float, default=0.2, help="Packet loss rate (0.0 to 1.0)")
    parser.add_argument("--corruption-rate", type=float, default=0.1, help="Packet corruption rate (0.0 to 1.0)")
    parser.add_argument("--delay-min", type=float, default=0.05, help="Minimum network delay in seconds")
    parser.add_argument("--delay-max", type=float, default=0.2, help="Maximum network delay in seconds")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout for ACK in seconds")
    parser.add_argument("--retries", type=int, default=3, help="Maximum retransmission attempts")
    
    args = parser.parse_args()
    
    # Print simulation parameters
    print_simulation_header(args)
    print(f"• Message: '{args.message}'")
    
    # Create and use client
    client = RUDPClient(
        server_host=args.server,
        server_port=args.port,
        loss_rate=args.loss_rate,
        corruption_rate=args.corruption_rate,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        timeout=args.timeout,
        max_retries=args.retries
    )
    
    try:
        success = client.send_message(args.message)
        if success:
            print(f"\nMessage sent successfully")
        else:
            print(f"\nFailed to send message. Please check if the server is running.")
    except KeyboardInterrupt:
        print(f"\nClient interrupted by user")
    finally:
        client.close()

if __name__ == "__main__":
    main() 