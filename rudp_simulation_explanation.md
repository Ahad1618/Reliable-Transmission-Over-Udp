# RUDP Simulation: Code Flow Explanation

## Overview

The `rudp_simulation.py` file provides a visual simulation of the Reliable UDP (RUDP) protocol. It demonstrates how reliability mechanisms like sequence numbering, acknowledgments, timeouts, and retransmissions work over an unreliable channel.

## Key Components

The simulation consists of four main classes:

1. **RUDPPacket**: Represents the data packets exchanged between client and server
2. **NetworkSimulator**: Simulates network conditions including delays, packet loss, and corruption
3. **SimulationVisualizer**: Provides visual feedback through colored console output
4. **RUDPSimulation**: Orchestrates the simulation by running client and server logic

## Program Flow

### 1. Initialization

When the program starts, it:
1. Parses command-line arguments to configure simulation parameters
2. Initializes the simulation with specified network conditions
3. Sets up communication channels between client and server

```
main() → RUDPSimulation(loss_rate, corruption_rate, etc.) → start(message)
```

### 2. Message Processing

The message is broken into small chunks (5 bytes each by default) to demonstrate packet-based transmission:

```python
chunk_size = 5  # Small size for demonstration
chunks = [message[i:i+chunk_size] for i in range(0, len(message), chunk_size)]
```

### 3. Concurrent Execution

The simulation runs client and server components concurrently:
- The server runs in a separate thread (`server_thread`)
- The client runs in the main thread

### 4. Client Operation

For each message chunk, the client:
1. Creates a packet with sequence number and data
2. Sends the packet through the simulated network
3. Waits for acknowledgment (ACK)
4. Retransmits on timeout if no ACK is received
5. Moves to the next chunk when ACK is received

```
run_client() → for each chunk → send packet → wait for ACK → increment sequence
```

### 5. Server Operation

The server continuously:
1. Checks for incoming packets
2. Verifies packet integrity using checksums
3. Processes packets in sequence order
4. Sends acknowledgments (ACKs) back to the client
5. Handles duplicate packets by resending ACKs

```
run_server() → while running → process packets → send ACKs → store data
```

### 6. Network Simulation

For each packet transmission, the network simulator:
1. May drop the packet based on `loss_rate`
2. Introduces random delay between `delay_min` and `delay_max`
3. May corrupt the packet based on `corruption_rate`

```
simulate_packet_transfer() → simulate loss → simulate delay → simulate corruption
```

### 7. Reliability Mechanisms

The simulation demonstrates these reliability features:

#### Sequence Numbers
- Each packet has a sequence number
- Server expects packets in order (tracks `server_expected_sequence`)
- Client assigns increasing sequence numbers (`client_next_sequence`)

#### Acknowledgments (ACKs)
- Server sends ACK for each correctly received packet
- Client waits for ACK before sending next packet

#### Timeouts and Retransmissions
- Client sets a timer after sending a packet
- If ACK not received within timeout, packet is retransmitted
- Client retries up to `max_retries` times

#### Duplicate Detection
- Server detects duplicate packets (sequence < expected)
- Duplicate packets get ACKs but aren't processed again

#### Error Detection
- Packets include a checksum for data integrity
- Corrupted packets are detected and discarded

### 8. Visualization

The `SimulationVisualizer` provides color-coded output for clarity:
- **Green**: Outgoing data packets
- **Cyan**: Outgoing ACKs
- **Yellow**: Incoming data packets
- **Blue**: Incoming ACKs
- **Red**: Dropped packets and timeouts
- **Magenta**: Corrupted packets

### 9. Completion

When all packets are transmitted:
1. Client signals completion (`client_done = True`)
2. Server completes processing of remaining packets
3. Simulation displays summary statistics:
   - Original message
   - Received message
   - Transmission success status

## Message Flow Example

A typical message exchange follows this pattern:

1. **CLIENT → SERVER**: Packet with SEQ=0, Data="Hello"
2. *Network may drop, delay, or corrupt the packet*
3. **SERVER → CLIENT**: ACK for SEQ=0
4. *Network may drop, delay, or corrupt the ACK*
5. **CLIENT → SERVER**: Packet with SEQ=1, Data=", RUD"
6. (And so on...)

If a packet or ACK is lost, the process includes timeouts and retransmissions.

## Conclusion

The simulation provides a clear visualization of how RUDP achieves reliability over unreliable networks. It demonstrates:

1. How sequence numbers and ACKs ensure reliable, ordered delivery
2. How timeouts and retransmission recover from packet loss
3. How checksums detect corruption
4. How duplicate detection prevents processing the same data twice

These mechanisms transform unreliable UDP communication into a reliable protocol suitable for applications requiring data integrity. 