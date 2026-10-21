"""Rank LAN IPv4 candidates so WSL/Docker/Hyper-V adapters never win by accident."""
from __future__ import annotations

import ipaddress
import re
import socket

import psutil

PRIVATE = tuple(ipaddress.ip_network(x) for x in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
# Names used by Windows for software adapters that are not reachable from a tablet.
VIRTUAL = re.compile(
    r"(vethernet|wsl|docker|hyper-?v|vmware|vmnet|virtualbox|vbox|loopback|npcap|tap-|tun\d|"
    r"tailscale|zerotier|hamachi|openvpn|wireguard|bluetooth|default switch|teredo|isatap)",
    re.IGNORECASE,
)
PHYSICAL = re.compile(r"(wlan|wi-?fi|wireless|ethernet|以太网|无线|本地连接|en\d|eth\d|wlp)", re.IGNORECASE)


def private_ipv4(value):
    """Return a usable private IPv4, excluding loopback, link-local and public addresses."""
    try:
        address = ipaddress.ip_address(value)
    except (ValueError, TypeError):
        return None
    if address.version != 4 or address.is_loopback or address.is_link_local or address.is_multicast:
        return None
    return address if any(address in network for network in PRIVATE) else None


def default_route_address():
    """Source address the OS would use for outbound traffic; a UDP connect sends no packet."""
    for target in ("192.0.2.1", "198.51.100.1"):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.2)
            sock.connect((target, 9))
            value = sock.getsockname()[0]
        except Exception:
            continue
        finally:
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass
        address = private_ipv4(value) if isinstance(value, str) else None
        if address is not None:
            return str(address)
    return None


def _score(name, address, route, up):
    virtual = bool(VIRTUAL.search(name or ""))
    score = 0 if virtual else 40
    if up:
        score += 15
    if route:
        if address == route:
            score += 60
        elif not virtual and _same_subnet(address, route):
            # A physical NIC on the routed subnet is the safest inbound target.
            score += 50
    return score - (60 if virtual else 0)


def _same_subnet(left, right):
    return ".".join(left.split(".")[:3]) == ".".join(right.split(".")[:3])


def candidates():
    """All usable private IPv4 addresses, best first, with adapter metadata for display."""
    route = default_route_address()
    stats = psutil.net_if_stats()
    rows, seen = [], set()
    for name, entries in psutil.net_if_addrs().items():
        for entry in entries:
            if entry.family != socket.AF_INET:
                continue
            address = private_ipv4(entry.address)
            if address is None or str(address) in seen:
                continue
            seen.add(str(address))
            up = bool(getattr(stats.get(name), "isup", False))
            rows.append({
                "address": str(address), "interface": name, "virtual": bool(VIRTUAL.search(name or "")),
                "up": up, "default_route": str(address) == route,
                "score": _score(name, str(address), route, up),
            })
    rows.sort(key=lambda row: (-row["score"], row["address"]))
    return rows


def rank(addresses):
    """Score an explicit address list (kept for callers that already enumerate adapters)."""
    try:
        known = {row["address"]: row for row in candidates()}
    except Exception:
        known = {}
    rows = []
    for value in addresses:
        address = private_ipv4(value)
        if address is None:
            continue
        key = str(address)
        rows.append(known.get(key) or {
            "address": key, "interface": "", "virtual": False, "up": True,
            "default_route": False, "score": 0,
        })
    rows.sort(key=lambda row: (-row["score"], row["address"]))
    return rows


def pick(preferred=None):
    """Choose the preferred address if still present, else the best candidate."""
    rows = candidates()
    if preferred:
        for row in rows:
            if row["address"] == preferred:
                return row["address"], rows
        return None, rows
    return (rows[0]["address"] if rows else None), rows


def all_private():
    """Loopback plus every private adapter address; used for Host header allow-listing."""
    return ["127.0.0.1"] + [row["address"] for row in candidates()]


def label(row):
    parts = [row["address"], row["interface"] or "未知网卡"]
    if row.get("virtual"):
        parts.append("虚拟网卡")
    if row.get("default_route"):
        parts.append("默认路由")
    if not row.get("up", True):
        parts.append("未连接")
    return " · ".join(parts)
