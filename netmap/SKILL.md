---
name: netmap
description: Show all network interfaces, LAN neighbors, and Tailscale peers on the current machine. Use when the user asks about network status, neighbors, connected devices, or Tailscale peers.
allowed-tools: Bash
---

# netmap

Display a summary of all networks and their neighbors on the current machine.

## Usage

Run the netmap script:

```bash
python3 SKILL_DIR/scripts/netmap.py
```

Replace `SKILL_DIR` with the resolved skill directory path.

The script shows:
1. **Network interfaces** — all active interfaces with their IP addresses
2. **LAN neighbors** — devices discovered via ARP
3. **Tailscale peers** — if Tailscale is installed, shows all peers with status

Output is formatted as aligned tables for readability.
