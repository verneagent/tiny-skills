---
name: network-debug
description: Systematic home network speed diagnosis — WiFi, Ethernet, mesh, ISP. Covers TP-Link router API reverse engineering, channel congestion, PHY rate analysis, and physical placement debugging. Use when the user reports slow network, wants to diagnose internet speed, or needs to understand WiFi bottlenecks.
allowed-tools: Bash
---

# Network Debug

Systematically diagnose home network speed issues. The methodology: eliminate variables one layer at a time, from client → WiFi → router → ISP.

## Core Principle

**Always compare wired vs wireless.** A single Ethernet speed test can rule out 90% of variables. Until you have a wired baseline, any WiFi measurement is inconclusive.

```
WiFi test:  130 Mbps  ← could be WiFi, router, ONT, or ISP
Wired test: 938 Mbps  ← ISP is fine, bottleneck is WiFi
```

## Diagnostic Ladder

Work from closest to furthest:

1. **WiFi PHY metrics** (macOS: Option+click WiFi icon)
   - RSSI (signal), Noise, Tx Rate, MCS Index, Channel, PHY Mode
   - PHY rate × 0.4-0.6 ≈ expected real-world throughput

2. **Which AP is the client connected to?** (mesh systems)
   - TP-Link mesh: API or Web UI → filter devices by router node
   - A client near a mesh node might actually be connected to a distant AP

3. **Channel scan** (`system_profiler SPAirPortDataType`)
   - Look for co-channel interference (same channel, different SSID)
   - 5GHz at 160MHz by neighbors will bleed into adjacent channels

4. **Wired test** — plug Ethernet, run `speedtest-cli`
   - If wired speed matches plan → WiFi is the bottleneck
   - If wired is also slow → router/ONT/ISP is the bottleneck

5. **ONT inspection** — check the optic modem's port speed (FE 100M vs GE 1000M)

## WiFi PHY Rate Reference (802.11ax WiFi 6)

| MCS Index | 80MHz 2x2 PHY Rate | Typical Real |
|-----------|-------------------|--------------|
| 11 (max)  | 1201 Mbps        | 500-700 Mbps |
| 9         | 1032 Mbps        | 400-550 Mbps |
| 7         | 774 Mbps         | 300-400 Mbps |
| 5         | 576 Mbps         | 200-300 Mbps |
| 3         | 344 Mbps         | 120-180 Mbps |

MCS drops when RSSI is weak or interference is high. At -30 dBm you get MCS 11. At -60 dBm you get MCS 5.

## Physical Obstruction — The 5GHz Killer

**5GHz WiFi is extremely sensitive to obstructions.** A wooden desk can attenuate 24 dB of signal, dropping PHY rate from 1201 → 576 Mbps and real speed from 500 → 130 Mbps.

- Wooden desk/table: 20-30 dB loss possible (density, thickness, metal frame)
- Glass: 3-8 dB
- Drywall: 3-5 dB
- Concrete/brick: 30-50 dB

**If a mesh node is "nearby" but under a desk → it's effectively in another room at 5GHz.**

## TP-Link Router API

For TL-XDR / Archer / EasyMesh routers with the modern web UI:

### Login
```
POST http://192.168.0.1/
Content-Type: application/json
{"method":"do","login":{"password":"<securityEncode(password)>"}}
→ {"error_code":0, "stok":"<token>"}
```

### Password encoding (reverse-engineered from class.js)
```javascript
function securityEncode(input, key1, key2) {
  // key1 = "RDpbLfCPsJZ7fiv"
  // key2 = "yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriW..."
  let result = '';
  const maxLen = Math.max(input.length, key1.length);
  for (let m = 0; m < maxLen; m++) {
    let k = 187, l = 187;
    if (m >= input.length) l = key1.charCodeAt(m);
    else if (m >= key1.length) k = input.charCodeAt(m);
    else { k = input.charCodeAt(m); l = key1.charCodeAt(m); }
    result += key2.charAt((k ^ l) % key2.length);
  }
  return result;
}
```

### API Queries (after login)
```
POST http://192.168.0.1/stok=<stok>/ds
{"<module>":{...},"method":"get"}
```

Key modules:
- `hosts_info` (`{"table":"host_info"}`) — connected devices with MAC, IP, wifi_mode
- `function` (`{"name":["new_module_spec"]}`) — router capabilities (eth_bandwidth, mesh role, etc.)
- `system` (`{"name":["sys"]}`) — basic system info

**Critical gotcha**: stok from login is already URL-encoded. Do NOT encode again.

### wifi_mode values
- `"0"` = 2.4GHz WiFi (but also misreports Ethernet devices!)
- `"1"` = 5GHz WiFi
- `"2"` = Ethernet (rarely reported correctly)

### CLI Tool
```
node tplink-cli/tplink.js -p <password> status
```
Shows router specs, mesh status, and all connected devices with band.

## Common Pitfalls

1. **System profiler shows "Network Service Inactive"** — sandbox restriction. Retry with `--noproxy '*'` or disable sandbox.
2. **airport command missing on macOS 15+** — use Option+click WiFi icon or `system_profiler SPAirPortDataType`.
3. **`speedtest-cli` from Homebrew picks international servers in China** — use `--server` flag with a Chinese server ID.
4. **TP-Link API `wifi_mode` lies about Ethernet** — all wired devices show as `"0"` (2.4G). Trust the user's physical verification.
5. **Double NAT is often harmless for speed** — the overhead is negligible (1-2 ms). Only matters for port forwarding.

## Quick macOS Commands

```bash
# WiFi diagnostics
system_profiler SPAirPortDataType | grep -E "PHY|Channel|Signal|Rate|MCS"

# Speed test (Python version, works globally)
speedtest-cli --simple

# Speed test against specific server
speedtest-cli --server 24447 --simple  # Shanghai Unicom

# List nearby speedtest servers
speedtest-cli --list | grep -i china
```
