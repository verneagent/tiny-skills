#!/usr/bin/env python3
"""netmap - Show all networks and their neighbors as markdown tables."""

import re
import subprocess
from collections import defaultdict


def run(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout


def get_my_ips() -> set[str]:
    ips = set()
    for line in run("ifconfig").splitlines():
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", line)
        if m:
            ips.add(m.group(1))
    return ips


def subnet(ip: str) -> str:
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.x"
    return "other"


def is_special(ip: str) -> bool:
    return ip.endswith(".255") or ip.startswith("224.") or ip.startswith("239.")


def show_interfaces():
    print("**Interfaces**\n")
    print("| Interface | IP | Note |")
    print("|---|---|---|")
    iface = ""
    for line in run("ifconfig").splitlines():
        m = re.match(r"^(\w+):", line)
        if m:
            iface = m.group(1)
        m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", line)
        if m:
            ip = m.group(1)
            note = ""
            if ip == "127.0.0.1":
                note = "loopback"
            elif ip.startswith("100."):
                note = "tailscale"
            print(f"| {iface} | {ip} | {note} |")
    print()


def show_arp():
    my_ips = get_my_ips()
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for line in run("arp -a").splitlines():
        m = re.match(r"\? \((.+?)\) at (.+?) on (\w+)", line)
        if m:
            ip, mac, _iface = m.groups()
            if "incomplete" not in mac and not is_special(ip):
                groups[subnet(ip)].append((ip, mac))

    if not groups:
        print("**LAN Neighbors**: none\n")
        return

    total = sum(len(v) for v in groups.values())

    for net in sorted(groups.keys()):
        entries = groups[net]
        print(f"**{net}** ({len(entries)} devices)\n")
        print("| IP | MAC | Note |")
        print("|---|---|---|")
        for ip, mac in sorted(entries, key=lambda x: [int(p) for p in x[0].split(".")]):
            tag = ""
            if ip in my_ips:
                tag = "self"
            elif ip.endswith(".1"):
                tag = "gateway?"
            print(f"| {ip} | {mac} | {tag} |")
        print()

    print(f"Total: **{total}** LAN neighbors\n")


def show_tailscale():
    ts = run("tailscale status 2>/dev/null")
    if not ts.strip():
        ts = run(
            "/Applications/Tailscale.app/Contents/MacOS/Tailscale status 2>/dev/null"
        )
    if not ts.strip():
        return

    print("**Tailscale**\n")
    print("| IP | Name | OS | Status |")
    print("|---|---|---|---|")
    for line in ts.strip().splitlines():
        parts = line.split()
        if len(parts) >= 4:
            ip, name, _user, os_ = parts[0], parts[1], parts[2], parts[3]
            status = " ".join(parts[4:])
            print(f"| {ip} | {name} | {os_} | {status} |")
    print()


def main():
    show_interfaces()
    show_arp()
    show_tailscale()


if __name__ == "__main__":
    main()
