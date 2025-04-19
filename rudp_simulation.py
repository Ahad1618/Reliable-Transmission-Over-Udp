import socket
import json
import time
import random
import threading
import argparse
import sys
from datetime import datetime
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored terminal output
init()

class RUDPPacket:
    """Class representing a RUDP packet for simulation"""
    
    def __init__(self, sequence=0, data="", is_ack=False, ack_number=None):
        self.sequence = sequence
        self.data = data
        self.is_ack = is_ack
        self.ack_number = ack_number
        self.checksum = self._calculate_checksum(data) if not is_ack else 0
        self.timestamp = time.time()
        self.is_corrupted = False
    
    def to_json(self):
        """Convert packet to JSON"""
        packet_dict = {
            "sequence": self.sequence,
            "is_ack": self.is_ack,
            "checksum": self.checksum,
            "timestamp": self.timestamp
        }
        
        if self.is_ack:
            packet_dict["ack_number"] = self.ack_number
        else:
            packet_dict["data"] = self.data
            
        return json.dumps(packet_dict)
    
    @staticmethod
    def from_json(json_str):
        """Create packet from JSON string"""
        try:
            packet_dict = json.loads(json_str)
            packet = RUDPPacket()
            packet.sequence = packet_dict.get("sequence", 0)
            packet.is_ack = packet_dict.get("is_ack", False)
            packet.checksum = packet_dict.get("checksum", 0)
            packet.timestamp = packet_dict.get("timestamp", time.time())
            
            if packet.is_ack:
                packet.ack_number = packet_dict.get("ack_number")
                packet.data = ""
            else:
                packet.data = packet_dict.get("data", "")
                packet.ack_number = None
                
            return packet
        except json.JSONDecodeError:
            # Return a corrupted packet indicator
            packet = RUDPPacket()
            packet.is_corrupted = True
            return packet
    
    def _calculate_checksum(self, data):
        """Calculate a simple checksum for the data"""
        return sum(ord(c) for c in data) % 65536
    
    def verify_checksum(self):
        """Verify the integrity of the packet"""
        if self.is_ack:
            return True  # ACKs don't need checksum verification
            
        calculated_checksum = self._calculate_checksum(self.data)
        return calculated_checksum == self.checksum


class NetworkSimulator:
    """Simulates network conditions like delay, packet loss, and corruption"""
    
    def __init__(self, loss_rate=0.2, corruption_rate=0.1, delay_min=0.01, delay_max=0.1):
        self.loss_rate = loss_rate
        self.corruption_rate = corruption_rate
        self.delay_min = delay_min
        self.delay_max = delay_max
        
    def simulate_packet_transfer(self, packet):
        """Simulate network conditions for a packet"""
        # Simulate packet loss
        if random.random() < self.loss_rate:
            return None
            
        # Simulate network delay
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
        
        # Simulate packet corruption
        if random.random() < self.corruption_rate:
            # Corrupt the packet by changing checksum
            packet.checksum = random.randint(0, 65535)
            
        return packet


class SimulationVisualizer:
    """Visualizes the packet transfer process in the terminal"""
    
    def __init__(self, show_dropped=True, show_corrupted=True):
        self.show_dropped = show_dropped
        self.show_corrupted = show_corrupted
        
    def log_sent_packet(self, sender, packet, is_retransmission=False):
        """Log sent packet"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if packet.is_ack:
            print(f"{Fore.CYAN}{timestamp} {sender} → ACK {packet.ack_number}{' (RETRANSMIT)' if is_retransmission else ''}{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}{timestamp} {sender} → SEQ {packet.sequence} ['{packet.data}']{' (RETRANSMIT)' if is_retransmission else ''}{Style.RESET_ALL}")
    
    def log_received_packet(self, receiver, packet):
        """Log received packet"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if packet.is_ack:
            print(f"{Fore.BLUE}{timestamp} {receiver} ← ACK {packet.ack_number}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}{timestamp} {receiver} ← SEQ {packet.sequence} ['{packet.data}']{Style.RESET_ALL}")
    
    def log_dropped_packet(self, packet):
        """Log dropped packet"""
        if not self.show_dropped:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if packet.is_ack:
            print(f"{Fore.RED}{timestamp} ✗ DROPPED ACK {packet.ack_number}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{timestamp} ✗ DROPPED SEQ {packet.sequence}{Style.RESET_ALL}")
    
    def log_corrupted_packet(self, receiver, packet):
        """Log corrupted packet"""
        if not self.show_corrupted:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if packet.is_ack:
            print(f"{Fore.MAGENTA}{timestamp} {receiver} ← CORRUPTED ACK{Style.RESET_ALL}")
        else:
            print(f"{Fore.MAGENTA}{timestamp} {receiver} ← CORRUPTED SEQ {packet.sequence}{Style.RESET_ALL}")
    
    def log_timeout(self, sender, sequence):
        """Log timeout"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{Fore.RED}{timestamp} {sender} ! TIMEOUT SEQ {sequence}{Style.RESET_ALL}")
    
    def log_info(self, message):
        """Log general information"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{Fore.WHITE}{timestamp} ℹ {message}{Style.RESET_ALL}")


class RUDPSimulation:
    """Simulates RUDP communication between client and server"""
    
    def __init__(self, 
                 loss_rate=0.2, 
                 corruption_rate=0.1,
                 delay_min=0.05,
                 delay_max=0.2,
                 timeout=1.0,
                 max_retries=3,
                 window_size=1):  # For simplicity, default window size is 1
        
        self.network = NetworkSimulator(loss_rate, corruption_rate, delay_min, delay_max)
        self.visualizer = SimulationVisualizer()
        self.timeout = timeout
        self.max_retries = max_retries
        self.window_size = window_size
        
        # Communication channels (simulated)
        self.client_to_server = []
        self.server_to_client = []
        
        # State variables
        self.server_expected_sequence = 0
        self.client_next_sequence = 0
        self.client_acks_received = set()
        self.server_received_data = []
        
        # Control flags
        self.running = False
        self.client_done = False
        
    def start(self, message="Hello, RUDP! This is a test of reliable communication over unreliable channels."):
        """Start the simulation"""
        self.running = True
        
        # Break message into chunks
        chunk_size = 5  # Small size for demonstration
        chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
        
        # Start server thread
        server_thread = threading.Thread(target=self.run_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Run client in main thread
        self.run_client(chunks)
        
        # Wait for server to process all data
        time.sleep(1)
        self.running = False
        server_thread.join(timeout=1)
        
        # Show received message
        received_message = "".join(self.server_received_data)
        self.visualizer.log_info(f"Simulation complete")
        self.visualizer.log_info(f"Original message: '{message}'")
        self.visualizer.log_info(f"Received message: '{received_message}'")
        self.visualizer.log_info(f"Transmission successful: {message == received_message}")
        
    def run_client(self, chunks):
        """Run the client simulation"""
        self.visualizer.log_info("Starting RUDP Client")
        
        for chunk in chunks:
            # Create and send packet
            packet = RUDPPacket(sequence=self.client_next_sequence, data=chunk)
            retries = 0
            sent = False
            
            while not sent and retries < self.max_retries:
                # Send packet
                self.visualizer.log_sent_packet("CLIENT", packet, is_retransmission=(retries > 0))
                simulated_packet = self.network.simulate_packet_transfer(packet)
                
                if simulated_packet is None:
                    # Packet was dropped
                    self.visualizer.log_dropped_packet(packet)
                    retries += 1
                    time.sleep(self.timeout)
                    continue
                    
                # Add to server's incoming queue
                self.client_to_server.append(simulated_packet)
                
                # Wait for ACK with timeout
                ack_received = False
                start_time = time.time()
                
                while time.time() - start_time < self.timeout and not ack_received:
                    # Check for ACKs
                    if self.client_next_sequence in self.client_acks_received:
                        ack_received = True
                        self.client_acks_received.remove(self.client_next_sequence)
                        break
                    time.sleep(0.01)
                
                if ack_received:
                    # ACK received, move to next sequence
                    self.client_next_sequence += 1
                    sent = True
                else:
                    # Timeout, retry
                    self.visualizer.log_timeout("CLIENT", packet.sequence)
                    retries += 1
            
            if not sent:
                self.visualizer.log_info(f"Failed to send chunk '{chunk}' after {self.max_retries} retries")
                return
        
        self.client_done = True
        self.visualizer.log_info("Client done sending all chunks")
        
    def run_server(self):
        """Run the server simulation"""
        self.visualizer.log_info("Starting RUDP Server")
        
        while self.running:
            # Process any packets in the server's incoming queue
            if self.client_to_server:
                # Get next packet
                packet_json = self.client_to_server.pop(0)
                
                # Verify packet integrity
                if not packet_json.verify_checksum():
                    self.visualizer.log_corrupted_packet("SERVER", packet_json)
                    continue
                    
                # Log received packet
                self.visualizer.log_received_packet("SERVER", packet_json)
                
                # Check if this is the packet we're expecting
                if packet_json.sequence == self.server_expected_sequence:
                    # Process the packet (add to received data)
                    self.server_received_data.append(packet_json.data)
                    
                    # Send ACK
                    ack_packet = RUDPPacket(is_ack=True, ack_number=packet_json.sequence)
                    self.visualizer.log_sent_packet("SERVER", ack_packet)
                    
                    # Simulate network for ACK
                    simulated_ack = self.network.simulate_packet_transfer(ack_packet)
                    
                    if simulated_ack is None:
                        # ACK was dropped
                        self.visualizer.log_dropped_packet(ack_packet)
                    else:
                        # Add to client's incoming queue
                        self.server_to_client.append(simulated_ack)
                        self.client_acks_received.add(packet_json.sequence)
                    
                    # Increment expected sequence
                    self.server_expected_sequence += 1
                else:
                    # This is a duplicate or out-of-order packet
                    # For duplicates (packets with lower sequence numbers), still send ACK
                    if packet_json.sequence < self.server_expected_sequence:
                        self.visualizer.log_info(f"Duplicate packet with SEQ {packet_json.sequence}, expected {self.server_expected_sequence}")
                        
                        # Send ACK for the duplicate
                        ack_packet = RUDPPacket(is_ack=True, ack_number=packet_json.sequence)
                        self.visualizer.log_sent_packet("SERVER", ack_packet)
                        
                        # Simulate network for ACK
                        simulated_ack = self.network.simulate_packet_transfer(ack_packet)
                        
                        if simulated_ack is None:
                            # ACK was dropped
                            self.visualizer.log_dropped_packet(ack_packet)
                        else:
                            # Add to client's incoming queue
                            self.server_to_client.append(simulated_ack)
                            self.client_acks_received.add(packet_json.sequence)
            
            # If client is done and no more packets to process, exit
            if self.client_done and not self.client_to_server:
                if len(self.server_received_data) == self.server_expected_sequence:
                    break
            
            # Small sleep to avoid busy waiting
            time.sleep(0.01)


def main():
    parser = argparse.ArgumentParser(description="RUDP Simulation")
    parser.add_argument("--message", default="Hello, RUDP! This is a test of reliable communication.", 
                        help="Message to transmit")
    parser.add_argument("--loss-rate", type=float, default=0.2, 
                        help="Packet loss rate (0.0 to 1.0)")
    parser.add_argument("--corruption-rate", type=float, default=0.1, 
                        help="Packet corruption rate (0.0 to 1.0)")
    parser.add_argument("--delay-min", type=float, default=0.05, 
                        help="Minimum network delay in seconds")
    parser.add_argument("--delay-max", type=float, default=0.2, 
                        help="Maximum network delay in seconds")
    parser.add_argument("--timeout", type=float, default=1.0, 
                        help="Timeout for ACK in seconds")
    parser.add_argument("--retries", type=int, default=3, 
                        help="Maximum retransmission attempts")
    
    args = parser.parse_args()
    
    # Print simulation parameters
    print(f"{Fore.WHITE}╔══════════════════════════════════════════════════╗")
    print(f"║            RUDP PROTOCOL SIMULATION              ║")
    print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Parameters:{Style.RESET_ALL}")
    print(f"• Loss Rate: {args.loss_rate:.1%}")
    print(f"• Corruption Rate: {args.corruption_rate:.1%}")
    print(f"• Network Delay: {args.delay_min:.2f}s to {args.delay_max:.2f}s")
    print(f"• Timeout: {args.timeout:.2f}s")
    print(f"• Max Retries: {args.retries}")
    print(f"• Message: '{args.message}'")
    print(f"\n{Fore.WHITE}╔══════════════════════════════════════════════════╗")
    print(f"║                 SIMULATION LOG                   ║")
    print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    # Create and start simulation
    simulation = RUDPSimulation(
        loss_rate=args.loss_rate,
        corruption_rate=args.corruption_rate,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        timeout=args.timeout,
        max_retries=args.retries
    )
    
    simulation.start(args.message)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Simulation interrupted by user{Style.RESET_ALL}")
        sys.exit(0) 