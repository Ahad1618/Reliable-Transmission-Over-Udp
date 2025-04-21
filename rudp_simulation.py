import json
import time
import random
import argparse
import sys
from datetime import datetime
from colorama import Fore, Back, Style, init

# Initialize colorama for cross-platform colored terminal output
init()

class RUDPPacket:
    """Class representing a RUDP packet"""
    
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
        
    def should_drop_packet(self):
        """Determine if a packet should be dropped"""
        return random.random() < self.loss_rate
    
    def should_corrupt_packet(self):
        """Determine if a packet should be corrupted"""
        return random.random() < self.corruption_rate
    
    def get_delay(self):
        """Get a random network delay"""
        return random.uniform(self.delay_min, self.delay_max)


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

def print_simulation_header(args=None):
    """Print simulation parameters"""
    print(f"{Fore.WHITE}╔══════════════════════════════════════════════════╗")
    print(f"║            RUDP PROTOCOL IMPLEMENTATION           ║")
    print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    if args:
        print(f"{Fore.CYAN}Parameters:{Style.RESET_ALL}")
        print(f"• Loss Rate: {args.loss_rate:.1%}")
        print(f"• Corruption Rate: {args.corruption_rate:.1%}")
        print(f"• Network Delay: {args.delay_min:.2f}s to {args.delay_max:.2f}s")
        
        # Only print timeout and retries if they exist
        if hasattr(args, 'timeout'):
            print(f"• Timeout: {args.timeout:.2f}s")
        if hasattr(args, 'retries'):
            print(f"• Max Retries: {args.retries}")
        
    print(f"\n{Fore.WHITE}╔══════════════════════════════════════════════════╗")
    print(f"║                 SIMULATION LOG                   ║")
    print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}") 