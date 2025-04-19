# 📦 Reliable UDP Transmission (Python – Single File)

A Python project that implements **reliable data transmission over UDP** in a **single script**, using custom acknowledgments, timeouts, and sequence numbers — mimicking the behavior of TCP over UDP.

---

## 🔍 Overview

UDP (User Datagram Protocol) is fast but unreliable — it doesn’t guarantee delivery, order, or duplication control. This project builds a basic **reliability mechanism** over UDP to ensure safe data transmission using:

- ✅ ACK-based confirmation
- ⏱️ Timeout and retransmission
- 🔢 Packet sequencing
- 🚫 Duplicate handling

---

## 📄 File

- `reliable_udp.py` – Contains both sender and receiver logic (configured by argument)

---

## ▶️ How to Use

### 📥 As Receiver (Server):

```bash
python reliable_udp.py receive
