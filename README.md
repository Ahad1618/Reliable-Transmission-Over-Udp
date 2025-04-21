# Socket-Based Reliable UDP (RUDP) Implementation

This project implements a **Reliable UDP Protocol (RUDP)** using real sockets in Python, enhancing standard UDP with mechanisms for ensuring reliable packet delivery, correct ordering, and loss recovery.

## Features

- **Real socket-based communication** between client and server
- **Reliable data transfer** using acknowledgments (ACKs) and retransmissions
- **Packet sequencing** to maintain order
- **Timeout mechanism** for lost packets
- **Duplicate detection and handling**
- **Error detection** using checksums
- **Network condition simulation** (packet loss, corruption, delay) for testing
- **Visual representation** of packet exchanges in the terminal

## Architecture

The implementation consists of three main components:

1. **rudp_simulation.py**: Common utilities (packet structure, network simulator, visualization)
2. **server.py**: Implements the RUDP server using sockets
3. **client.py**: Implements the RUDP client using sockets
4. **demo.py**: Combined client and server in a single script for easy demonstration

## How It Works

1. The **client** divides a message into small chunks and sends them as packets with sequence numbers
2. For each packet, the client waits for an acknowledgment (ACK) from the server
3. If an ACK is not received within a timeout period, the client retransmits the packet
4. The **server** verifies received packets and sends ACKs back to the client
5. The server handles duplicate packets and ensures ordered delivery
6. Both client and server simulate network conditions to test reliability

## Usage

### Quick Demonstration

The easiest way to see the protocol in action is to run the demo script:

```bash
python demo.py
```

This runs both client and server in a single process, simulating packet loss, corruption, and network delay.

### Running Separate Client and Server

#### Start the RUDP Server

```bash
python server.py --host 127.0.0.1 --port 5000 --loss-rate 0.2 --corruption-rate 0.1
```

#### Start the RUDP Client

```bash
python client.py --server 127.0.0.1 --port 5000 --message "Hello, RUDP!" --loss-rate 0.2 --corruption-rate 0.1
```

## Command-line Arguments

### Server Arguments
- `--host`: Host address to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 5000)
- `--loss-rate`: Packet loss rate (0.0 to 1.0, default: 0.2)
- `--corruption-rate`: Packet corruption rate (0.0 to 1.0, default: 0.1)
- `--delay-min`: Minimum network delay in seconds (default: 0.05)
- `--delay-max`: Maximum network delay in seconds (default: 0.2)
- `--duration`: Server runtime in seconds (default: 60)

### Client Arguments
- `--server`: Server IP address (default: 127.0.0.1)
- `--port`: Server port (default: 5000)
- `--message`: Message to send (default: "Hello, RUDP! This is a test of reliable communication.")
- `--loss-rate`: Packet loss rate (0.0 to 1.0, default: 0.2)
- `--corruption-rate`: Packet corruption rate (0.0 to 1.0, default: 0.1)
- `--delay-min`: Minimum network delay in seconds (default: 0.05)
- `--delay-max`: Maximum network delay in seconds (default: 0.2)
- `--timeout`: Timeout for ACK in seconds (default: 1.0)
- `--retries`: Maximum retransmission attempts (default: 3)

## Implementation Details

### Packet Structure

Each packet contains:
- Sequence number
- Data payload (for data packets)
- Acknowledgment number (for ACK packets)
- Checksum for error detection
- Timestamp for tracking

Packets are serialized as JSON for easy debugging and inspection.

### Reliability Mechanisms

- **Stop-and-Wait ARQ**: The client waits for an ACK before sending the next packet
- **Retransmission**: Packets are resent if an ACK is not received within a timeout
- **Checksums**: Used to detect corrupted packets
- **Sequence numbers**: Used to detect duplicates and maintain order

### Network Simulation

The implementation simulates network conditions to test reliability:
- **Packet Loss**: Random dropping of packets
- **Corruption**: Random corruption of packet data
- **Delay**: Random delay in packet transmission

## Requirements

- Python 3.6+
- **colorama** package for colored terminal output
  ```bash
  pip install colorama
  ```

## Future Improvements

- **Sliding window protocol** for better throughput
- **Congestion control** mechanisms
- **Flow control** to adjust to receiver's capabilities
- **Bi-directional communication** for more realistic applications
- **File transfer utility** to demonstrate the protocol with real files 