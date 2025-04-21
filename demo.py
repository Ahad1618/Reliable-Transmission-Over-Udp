import socket
import json
import time
import random
import argparse
import sys
import threading
from datetime import datetime
from colorama import Fore, Style, init

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
    
    def __init__(self, loss_rate=0.1, corruption_rate=0.05, delay_min=0.01, delay_max=0.1):
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


class Logger:
    """Logs simulation events with color coding"""
    
    def log_sent(self, sender, packet, is_retransmission=False):
        """Log sent packet"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if packet.is_ack:
            print(f"{Fore.CYAN}{timestamp} {sender} → ACK {packet.ack_number}{' (RETRANSMIT)' if is_retransmission else ''}{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}{timestamp} {sender} → SEQ {packet.sequence} ['{packet.data}']{' (RETRANSMIT)' if is_retransmission else ''}{Style.RESET_ALL}")
    
    def log_received(self, receiver, packet):
        """Log received packet"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if packet.is_ack:
            print(f"{Fore.BLUE}{timestamp} {receiver} ← ACK {packet.ack_number}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}{timestamp} {receiver} ← SEQ {packet.sequence} ['{packet.data}']{Style.RESET_ALL}")
    
    def log_dropped(self, packet):
        """Log dropped packet"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if packet.is_ack:
            print(f"{Fore.RED}{timestamp} ✗ DROPPED ACK {packet.ack_number}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{timestamp} ✗ DROPPED SEQ {packet.sequence}{Style.RESET_ALL}")
    
    def log_corrupted(self, receiver, packet):
        """Log corrupted packet"""
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


class RUDPServer:
    """RUDP Server implementation"""
    
    def __init__(self, loss_rate=0.1, corruption_rate=0.05, delay_min=0.02, delay_max=0.1):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('127.0.0.1', 5000))
        
        self.network = NetworkSimulator(loss_rate, corruption_rate, delay_min, delay_max)
        self.logger = Logger()
        self.expected_sequence = 0
        self.received_data = []
        self.running = False
    
    def start(self):
        """Start the server"""
        self.running = True
        self.logger.log_info("Server started on 127.0.0.1:5000")
        
        self.socket.settimeout(0.1)  # Short timeout to check if we should stop
        
        while self.running:
            try:
                # Wait for data from client
                json_data, client_address = self.socket.recvfrom(1024)
                
                # Simulate network conditions
                if self.network.should_drop_packet():
                    # Simulate packet loss
                    packet = RUDPPacket.from_json(json_data.decode())
                    self.logger.log_dropped(packet)
                    continue
                
                # Simulate network delay
                delay = self.network.get_delay()
                time.sleep(delay)
                
                # Process the packet
                packet = RUDPPacket.from_json(json_data.decode())
                
                # Simulate corruption
                if self.network.should_corrupt_packet():
                    packet.checksum = random.randint(0, 65535)  # Corrupt the checksum
                    self.logger.log_corrupted("SERVER", packet)
                    continue  # Discard corrupted packets
                
                # Log received packet
                self.logger.log_received("SERVER", packet)
                
                # Verify packet integrity
                if not packet.verify_checksum():
                    self.logger.log_corrupted("SERVER", packet)
                    continue
                
                # Process packet based on expected sequence
                if packet.sequence == self.expected_sequence:
                    # This is the packet we're expecting
                    self.received_data.append(packet.data)
                    
                    # Send ACK
                    self._send_ack(client_address, packet.sequence)
                    
                    # Update expected sequence
                    self.expected_sequence += 1
                    
                elif packet.sequence < self.expected_sequence:
                    # This is a duplicate packet, still send ACK
                    self.logger.log_info(f"Duplicate packet with SEQ {packet.sequence}, expected {self.expected_sequence}")
                    self._send_ack(client_address, packet.sequence)
                
            except socket.timeout:
                # Socket timeout - just continue the loop
                continue
            except Exception as e:
                if self.running:  # Only log if we're still running
                    self.logger.log_info(f"Server error: {str(e)}")
                continue
        
        # Print summary
        if self.received_data:
            received_message = "".join(self.received_data)
            self.logger.log_info(f"Received complete message: '{received_message}'")
        
        try:
            self.socket.close()
        except:
            pass
    
    def _send_ack(self, client_address, sequence):
        """Send acknowledgment for a sequence number"""
        ack_packet = RUDPPacket(is_ack=True, ack_number=sequence)
        
        # Log sent ACK
        self.logger.log_sent("SERVER", ack_packet)
        
        # Simulate packet loss for ACK
        if self.network.should_drop_packet():
            self.logger.log_dropped(ack_packet)
            return
        
        # Simulate network delay for ACK
        delay = self.network.get_delay()
        time.sleep(delay)
        
        # Send the ACK
        try:
            self.socket.sendto(ack_packet.to_json().encode(), client_address)
        except Exception as e:
            self.logger.log_info(f"Error sending ACK: {str(e)}")
    
    def stop(self):
        """Stop the server"""
        self.running = False
        try:
            self.socket.close()
        except:
            pass


class RUDPClient:
    """RUDP Client implementation"""
    
    def __init__(self, loss_rate=0.1, corruption_rate=0.05, delay_min=0.02, delay_max=0.1, timeout=1.0, max_retries=5):
        self.server_address = ('127.0.0.1', 5000)
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        
        self.network = NetworkSimulator(loss_rate, corruption_rate, delay_min, delay_max)
        self.logger = Logger()
        
        self.next_sequence = 0
        self.timeout = timeout
        self.max_retries = max_retries
    
    def send_message(self, message):
        """Send a message reliably using RUDP"""
        self.logger.log_info(f"Sending message to {self.server_address[0]}:{self.server_address[1]}")
        
        # Break message into chunks
        chunk_size = 5  # Small size for demonstration
        chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
        
        for chunk in chunks:
            # Create packet
            packet = RUDPPacket(sequence=self.next_sequence, data=chunk)
            retries = 0
            sent = False
            
            while not sent and retries < self.max_retries:
                # Simulate packet loss
                if self.network.should_drop_packet():
                    self.logger.log_sent("CLIENT", packet, is_retransmission=(retries > 0))
                    self.logger.log_dropped(packet)
                    retries += 1
                    time.sleep(self.timeout / 2)  # Wait a bit less than full timeout
                    continue
                
                # Simulate network delay
                delay = self.network.get_delay()
                time.sleep(delay)
                
                # Simulate corruption
                if self.network.should_corrupt_packet():
                    corrupted_packet = RUDPPacket(sequence=packet.sequence, data=packet.data)
                    corrupted_packet.checksum = random.randint(0, 65535)  # Corrupt the checksum
                    self.logger.log_sent("CLIENT", corrupted_packet, is_retransmission=(retries > 0))
                    self.socket.sendto(corrupted_packet.to_json().encode(), self.server_address)
                    retries += 1
                    time.sleep(self.timeout / 2)
                    continue
                
                # Log sent packet
                self.logger.log_sent("CLIENT", packet, is_retransmission=(retries > 0))
                
                # Send the packet
                try:
                    self.socket.sendto(packet.to_json().encode(), self.server_address)
                    
                    # Wait for ACK
                    try:
                        json_data, _ = self.socket.recvfrom(1024)
                        
                        # Simulate packet loss for ACK
                        if self.network.should_drop_packet():
                            ack_packet = RUDPPacket.from_json(json_data.decode())
                            self.logger.log_dropped(ack_packet)
                            retries += 1
                            continue
                        
                        # Process the ACK
                        ack_packet = RUDPPacket.from_json(json_data.decode())
                        
                        # Log received ACK
                        self.logger.log_received("CLIENT", ack_packet)
                        
                        # Verify this is the ACK we're expecting
                        if ack_packet.is_ack and ack_packet.ack_number == self.next_sequence:
                            self.next_sequence += 1
                            sent = True
                        else:
                            self.logger.log_info(f"Unexpected ACK number: {ack_packet.ack_number}, expected: {self.next_sequence}")
                    except socket.timeout:
                        self.logger.log_timeout("CLIENT", packet.sequence)
                        retries += 1
                except Exception as e:
                    self.logger.log_info(f"Client error: {str(e)}")
                    retries += 1
            
            if not sent:
                self.logger.log_info(f"Failed to send chunk '{chunk}' after {self.max_retries} retries")
                return False
        
        self.logger.log_info(f"Message sent successfully")
        return True
    
    def close(self):
        """Close the socket"""
        try:
            self.socket.close()
        except:
            pass


def run_demo():
    """Run a demonstration of the RUDP protocol"""
    print(f"{Fore.WHITE}╔══════════════════════════════════════════════════╗")
    print(f"║            RUDP PROTOCOL DEMONSTRATION           ║")
    print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}Parameters:{Style.RESET_ALL}")
    print(f"• Loss Rate: 10.0%")
    print(f"• Corruption Rate: 5.0%")
    print(f"• Network Delay: 0.02s to 0.10s")
    print(f"• Timeout: 1.00s")
    print(f"• Max Retries: 5")
    print(f"• Message: 'Hello, RUDP! This is a test.'")
    
    print(f"\n{Fore.WHITE}╔══════════════════════════════════════════════════╗")
    print(f"║                 SIMULATION LOG                   ║")
    print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}")
    
    # Create and start server in a separate thread
    server = RUDPServer()
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Give server a moment to start
    time.sleep(1)
    
    # Create and use client
    client = RUDPClient()
    
    try:
        success = client.send_message("Hello, RUDP! This is a test.")
        if success:
            print(f"\n{Fore.GREEN}Message sent successfully{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}Failed to send message{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
    finally:
        client.close()
        
    # Let server process any remaining packets
    time.sleep(2)
    server.stop()
    
    # Give server thread time to notice it's been stopped
    time.sleep(0.5)
    
    # Show received message
    received_message = "".join(server.received_data)
    print(f"\n{Fore.WHITE}Demonstration complete!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Sent message: 'Hello, RUDP! This is a test.'{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Received message: '{received_message}'{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Transmission successful: {'Yes' if received_message == 'Hello, RUDP! This is a test.' else 'No'}{Style.RESET_ALL}")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Demonstration interrupted by user{Style.RESET_ALL}")
        sys.exit(0) 