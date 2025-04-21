import socket
import argparse
import sys
import time
import random
import json
from rudp_simulation import RUDPPacket, NetworkSimulator, SimulationVisualizer, print_simulation_header

class RUDPServer:
    """RUDP Server implementation using real sockets"""
    
    def __init__(self, host="0.0.0.0", port=5000, 
                 loss_rate=0.2, corruption_rate=0.1, 
                 delay_min=0.05, delay_max=0.2):
        self.host = host
        self.port = port
        
        # Create a UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            self.socket.bind((host, port))
            self.visualizer = SimulationVisualizer()
            self.visualizer.log_info(f"Socket successfully bound to {host}:{port}")
        except Exception as e:
            print(f"Error binding socket: {str(e)}")
            sys.exit(1)
        
        # Setup network simulator for artificial conditions
        self.network = NetworkSimulator(loss_rate, corruption_rate, delay_min, delay_max)
        
        # Server state
        self.expected_sequence = 0
        self.received_data = []
        self.running = False
        self.clients = {}  # Track clients by address
    
    def start(self, duration=None):
        """Start the server and listen for incoming packets"""
        self.running = True
        self.visualizer.log_info(f"Server started on {self.host}:{self.port}")
        
        start_time = time.time()
        self.socket.settimeout(0.1)  # Short timeout for checking if we should stop
        
        while self.running:
            if duration and time.time() - start_time > duration:
                self.visualizer.log_info(f"Server stopping after {duration} seconds")
                break
                
            try:
                # Wait for data from client
                json_data, client_address = self.socket.recvfrom(1024)
                
                # Process the packet
                try:
                    packet = RUDPPacket.from_json(json_data.decode())
                    
                    # Handle ping packet (used by client to check if server is reachable)
                    if packet.data == "PING":
                        self.visualizer.log_info(f"Received ping from {client_address[0]}:{client_address[1]}")
                        # Send a pong response
                        pong_packet = RUDPPacket(sequence=0, data="PONG", is_ack=False)
                        self.socket.sendto(pong_packet.to_json().encode(), client_address)
                        continue
                    
                    # Add client to tracking if not seen before
                    if client_address not in self.clients:
                        self.clients[client_address] = {
                            "address": client_address,
                            "expected_sequence": 0,
                            "received_data": []
                        }
                        self.visualizer.log_info(f"New client connected: {client_address[0]}:{client_address[1]}")
                    
                    # Get client state
                    client = self.clients[client_address]
                    
                    # Simulate network conditions
                    if self.network.should_drop_packet():
                        # Simulate packet loss
                        self.visualizer.log_dropped_packet(packet)
                        continue
                    
                    # Simulate network delay
                    delay = self.network.get_delay()
                    time.sleep(delay)
                    
                    # Simulate corruption
                    if self.network.should_corrupt_packet():
                        packet.checksum = random.randint(0, 65535)  # Corrupt the checksum
                        self.visualizer.log_corrupted_packet("SERVER", packet)
                        continue  # Discard corrupted packets
                    
                    # Log received packet
                    self.visualizer.log_received_packet("SERVER", packet)
                    
                    # Verify packet integrity
                    if not packet.verify_checksum():
                        self.visualizer.log_corrupted_packet("SERVER", packet)
                        continue
                    
                    # Process packet based on expected sequence
                    if packet.sequence == client["expected_sequence"]:
                        # This is the packet we're expecting
                        client["received_data"].append(packet.data)
                        
                        # Send ACK
                        self._send_ack(client_address, packet.sequence)
                        
                        # Update expected sequence
                        client["expected_sequence"] += 1
                        
                    elif packet.sequence < client["expected_sequence"]:
                        # This is a duplicate packet, still send ACK
                        self.visualizer.log_info(f"Duplicate packet with SEQ {packet.sequence}, expected {client['expected_sequence']}")
                        self._send_ack(client_address, packet.sequence)
                    else:
                        # Out of order packet, ignore for this simple implementation
                        self.visualizer.log_info(f"Out of order packet with SEQ {packet.sequence}, expected {client['expected_sequence']}")
                
                except json.JSONDecodeError:
                    self.visualizer.log_info(f"Received invalid JSON data from {client_address[0]}:{client_address[1]}")
                except Exception as e:
                    self.visualizer.log_info(f"Error processing packet: {str(e)}")
                
            except socket.timeout:
                # Socket timeout - just continue the loop
                continue
            except (ConnectionResetError, ConnectionRefusedError) as e:
                self.visualizer.log_info(f"Connection error: {str(e)}")
                continue
            except Exception as e:
                self.visualizer.log_info(f"Error: {str(e)}")
                continue
        
        # Print summary for all clients
        for addr, client in self.clients.items():
            if client["received_data"]:
                received_message = "".join(client["received_data"])
                self.visualizer.log_info(f"Received complete message from {addr[0]}:{addr[1]}: '{received_message}'")
        
        if not self.clients:
            self.visualizer.log_info("No clients connected during this session")
        
        self.socket.close()
    
    def _send_ack(self, client_address, sequence):
        """Send acknowledgment for a sequence number"""
        ack_packet = RUDPPacket(is_ack=True, ack_number=sequence)
        
        # Log sent ACK
        self.visualizer.log_sent_packet("SERVER", ack_packet)
        
        # Simulate packet loss for ACK
        if self.network.should_drop_packet():
            self.visualizer.log_dropped_packet(ack_packet)
            return
            
        # Simulate network delay for ACK
        delay = self.network.get_delay()
        time.sleep(delay)
        
        # Send the ACK
        try:
            self.socket.sendto(ack_packet.to_json().encode(), client_address)
        except Exception as e:
            self.visualizer.log_info(f"Error sending ACK: {str(e)}")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass  # Ignore errors when closing


def main():
    parser = argparse.ArgumentParser(description="RUDP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--loss-rate", type=float, default=0.2, help="Packet loss rate (0.0 to 1.0)")
    parser.add_argument("--corruption-rate", type=float, default=0.1, help="Packet corruption rate (0.0 to 1.0)")
    parser.add_argument("--delay-min", type=float, default=0.05, help="Minimum network delay in seconds")
    parser.add_argument("--delay-max", type=float, default=0.2, help="Maximum network delay in seconds")
    parser.add_argument("--duration", type=int, default=60, help="Server runtime in seconds")
    
    args = parser.parse_args()
    
    # Print simulation parameters
    print_simulation_header(args)
    
    # Create and start server
    server = RUDPServer(
        host=args.host,
        port=args.port,
        loss_rate=args.loss_rate,
        corruption_rate=args.corruption_rate,
        delay_min=args.delay_min,
        delay_max=args.delay_max
    )
    
    try:
        server.start(duration=args.duration)
    except KeyboardInterrupt:
        print(f"\nServer interrupted by user")
    finally:
        server.stop()

if __name__ == "__main__":
    main() 