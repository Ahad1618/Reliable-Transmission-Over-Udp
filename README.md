# Reliable UDP Protocol (RUDP)

This project implements a **Reliable UDP Protocol (RUDP)** in Python, enhancing standard UDP with mechanisms for ensuring reliable packet delivery, correct ordering, and loss recovery.

## Features

- **Reliable data transfer** using acknowledgments (ACKs) and retransmissions
- **Packet sequencing** to maintain order
- **Timeout mechanism** for lost packets
- **Duplicate detection and handling**
- **Basic error detection** using checksums
- **File transfer utility** to demonstrate the protocol
- **Network simulation** for testing with packet loss and corruption
- **Visual simulation** of packet exchanges between client and server

## How It Works

1. The **sender (client)** assigns sequence numbers to packets, sends them, and waits for an **ACK**.
2. The **receiver (server)** receives packets, verifies sequence numbers, and sends ACKs back.
3. If the sender does not receive an ACK within a timeout, it **retransmits** the packet.
4. The receiver discards **duplicate packets** and ensures ordered delivery.

## Files in the Project

- `rudp_simulation.py`: Visual simulation of the RUDP protocol in action

```

#usage
**Send a test message:**
```bash
python rudp_test.py client --message "This is a test message" --loss-rate 0.2 --corruption-rate 0.1
```

### Visual Simulation

The `rudp_simulation.py` script provides a visual representation of the RUDP protocol in action, running both client and server in a single script with color-coded logs:

```bash
python rudp_simulation.py --message "Hello, RUDP!" --loss-rate 0.3 --corruption-rate 0.2
```

This simulation shows:
- Packet transmission with sequence numbers
- ACK exchanges
- Packet drops (simulated loss)
- Corruption and checksums
- Timeouts and retransmissions
- Duplicate packet handling

You can adjust the network conditions using these parameters:
- `--loss-rate`: Probability of packet loss (0.0 to 1.0)
- `--corruption-rate`: Probability of packet corruption (0.0 to 1.0)
- `--delay-min` and `--delay-max`: Network delay range in seconds
- `--timeout`: ACK timeout in seconds
- `--retries`: Maximum retransmission attempts

## Command-line Arguments


## Implementation Details

- Packets are serialized as JSON for easy debugging and inspection
- Basic checksum is used for error detection
- Files are transferred in chunks with base64 encoding
- Each packet has a sequence number for ordering and duplicate detection
- The test script uses a custom socket wrapper to simulate network conditions

## Limitations

This implementation is designed for educational purposes and has some limitations:

- Basic flow control (no sliding window)
- Simple checksum-based error detection
- No congestion control
- Limited to JSON-serializable data
- Not optimized for large file transfers

## Requirements

- Python 3.6+
- **colorama** package (only for the visual simulation)
  ```bash
  pip install colorama
  ```
- No other external dependencies 
