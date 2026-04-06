#!/usr/bin/env python3
"""
named_conf.py - Generate BIND named.conf and zone files from a config dict.

Converted from Bivio::Util::NamedConf (Perl) to Python.

Usage:
    python named_conf.py generate [txt1.json ...]  < config.py
    python named_conf.py root_file
"""

import ipaddress
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

ZONE_DIR = Path("var/named")
ROOT_FILE = "named.root"
INTERNIC_ROOT_URL = "https://www.internic.net/zones/named.root"


def _dot(name, origin=""):
    if name.endswith("."):
        return name
    if name == "@":
        if not origin:
            return name
        return origin if origin.endswith(".") else origin + "."
    if origin:
        name = f"{name}.{origin}"
    if not name.endswith("."):
        name += "."
    return name


def _newlines(*parts):
    return "\n".join(parts) + "\n"


def _cidr_hosts(cidr):
    net = ipaddress.IPv4Network(cidr, strict=False)
    yield from net


def _address_to_host_key(cidr, ip):
    net = ipaddress.IPv4Network(cidr, strict=False)
    parts = ip.split(".")
    # Split after the last fully-covered octet boundary
    if net.prefixlen < 8:
        host_parts = parts[1:]
    elif net.prefixlen < 16:
        host_parts = parts[2:]
    elif net.prefixlen < 24:
        host_parts = parts[2:]
    else:
        host_parts = parts[3:]
    if len(host_parts) == 1:
        return int(host_parts[0])
    return ".".join(host_parts)


def _map_host_addresses(cidr, callback):
    results = []
    for addr in _cidr_hosts(cidr):
        r = callback(str(addr))
        if r is not None:
            if isinstance(r, list):
                results.extend(r)
            else:
                results.append(r)
    return results


def _serial(cfg):
    server = cfg["servers"][0]
    try:
        out = subprocess.check_output(
            ["dig", "soa", server, f"@{server}"],
            text=True, stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise RuntimeError(f"{server}: dig failed: {e}") from e

    for line in out.splitlines():
        if line.startswith(";"):
            continue
        m = re.match(
            r"^\S+\s+\d+\s+IN\s+SOA\s+\S+\s+\S+\s+(\d{1,10})\s+\d", line
        )
        if m:
            s = int(m.group(1))
            today = date.today().strftime("%Y%m%d")
            n = int(today + "00")
            max_n = n + 99
            n = s + 1 if s >= n else n
            if n >= max_n:
                raise RuntimeError(
                    f"Too many updates today: curr={s} new={n} max={max_n}"
                )
            return n

    raise RuntimeError(f"{server}: could not find SOA")


def _zone_header(zone_dot, cfg):
    server0 = _dot(cfg["servers"][0], zone_dot.rstrip(".") + ".")
    hostmaster = _dot(cfg["hostmaster"], zone_dot.rstrip(".") + ".")
    soa = (
        f"@ IN SOA {server0} {hostmaster} ("
        f" {cfg['serial']}"
        f" {cfg['refresh']}"
        f" {cfg['retry']}"
        f" {cfg['expiry']}"
        f" {cfg['minimum']} )"
    )
    ns_records = [f"@ IN NS {_dot(s, zone_dot)}" for s in cfg["servers"]]
    return (f"$TTL {cfg['ttl']}", f"$ORIGIN {zone_dot}", soa, *ns_records)


def _zone_ipv4_map_array(ipv4_list):
    res = {}
    it = iter(ipv4_list)
    for key, val in zip(it, it):
        cidr, num = key
        cidr_dict = res.setdefault(cidr, {})
        if num in cidr_dict:
            raise ValueError(f"Duplicate host cidr={cidr} num={num}")
        cidr_dict[num] = val
    return res


def _normalize_host_entry(entry, cfg):
    if isinstance(entry, (list, tuple)):
        host, hcfg = entry[0], dict(entry[1]) if len(entry) > 1 else {}
    else:
        host = entry
        hcfg = {}

    if isinstance(host, str) and re.match(r"^@(?=[\w@])", host):
        host = host[1:]
        hcfg["ptr"] = True

    merged = {**cfg, **hcfg}
    if host == "@":
        host = cfg.get("_zone_dot", "@")
    return [host, merged]


def _zone_ipv4_map(zone, cfg, ptr_map, op):
    ipv4 = cfg.get("ipv4")
    if ipv4 is None:
        return []
    if isinstance(ipv4, list):
        ipv4 = _zone_ipv4_map_array(ipv4)
    if not isinstance(ipv4, dict):
        raise ValueError(f"Invalid ipv4 config: {ipv4!r}")

    results = []
    for cidr in sorted(ipv4):
        host_map = ipv4[cidr]
        net = ipaddress.IPv4Network(cidr, strict=False)

        def process_ip(ip_str, _cidr=cidr, _host_map=host_map):
            key = _address_to_host_key(_cidr, ip_str)
            hosts = _host_map.get(key)
            if hosts is None:
                return None
            if not isinstance(hosts, list):
                hosts = [hosts]
            out = []
            for entry in sorted(
                [_normalize_host_entry(e, cfg) for e in hosts],
                key=lambda x: x[0],
            ):
                r = op(entry[0], entry[1], ip_str, _cidr)
                if r is not None:
                    if isinstance(r, list):
                        out.extend(r)
                    else:
                        out.append(r)
            return out or None

        results.extend(_map_host_addresses(cidr, process_ip))
    return results


def _zone_a(zone, cfg, ptr_map):
    def op(host, host_cfg, ip, cidr):
        entry = ptr_map.setdefault(cidr, {}).setdefault(ip, {"yes": [], "no": []})
        key = "yes" if host_cfg.get("ptr") else "no"
        entry[key].append(_dot(host, zone))
        return f"{host} IN A {ip}"
    return _zone_ipv4_map(zone, cfg, ptr_map, op)


def _zone_mx(zone, cfg, ptr_map):
    def op(host, host_cfg, ip, cidr):
        mx = host_cfg.get("mx", host)
        if not mx:
            return None
        mx_list = mx if isinstance(mx, list) else [mx]
        out = []
        for entry in mx_list:
            if isinstance(entry, (list, tuple)):
                mx_host, mx_pref = entry[0], entry[1]
            else:
                mx_host = entry
                mx_pref = host_cfg.get("mx_pref", 10)
            out.append(f"{host} IN MX {mx_pref} {mx_host}")
        return out
    return _zone_ipv4_map(zone, cfg, ptr_map, op)


def _zone_spf1(zone, cfg, ptr_map):
    def op(host, host_cfg, ip, cidr):
        spf1 = host_cfg.get("spf1")
        if not spf1:
            return None
        global_spf1 = cfg.get("spf1", "")
        spf1 = spf1.replace("+", global_spf1)
        return f'{host} IN TXT "v=spf1 a mx {spf1} -all"'
    return _zone_ipv4_map(zone, cfg, ptr_map, op)


def _zone_literal(cfg_which, dns_which, transform, zone, cfg):
    values = cfg.get(cfg_which, [])
    dns_type = (dns_which or cfg_which).upper()
    transform = transform or (lambda v: v)

    if isinstance(values, dict):
        values = [[k, transform(v)] for k, v in sorted(values.items())]
    elif isinstance(values, list):
        values = [[item[0], transform(item[1])] for item in values]

    return [f"{host} IN {dns_type} {val}" for host, val in values]


def _zone_cname(zone, cfg, ptr_map):
    return _zone_literal("cname", None, None, zone, cfg)


def _zone_srv(zone, cfg, ptr_map):
    return _zone_literal("srv", None, None, zone, cfg)


def _zone_txt(zone, cfg, ptr_map):
    return _zone_literal("txt", None, None, zone, cfg)


def _zone_dkim1(zone, cfg, ptr_map):
    def dkim_transform(value):
        res = f'"v=DKIM1; k=rsa; p={value};"'
        if len(res) > 255:
            raise ValueError(
                f"dkim1 only supports 1024-bit keys (p={value}); "
                "use opendkim.json for longer records"
            )
        return res
    return _zone_literal("dkim1", "txt", dkim_transform, zone, cfg)


def _zone_txt_json(zone_dot, txt_json, ptr_map):
    zone_name = zone_dot.rstrip(".")
    records = txt_json.get(zone_name, [])
    return [f"{host} IN TXT {val}" for host, val in records]


def _zone(self_state, zone, zone_cfg, common, ptr_map):
    zone_dot = _dot(zone)
    cfg = {**common, **zone_cfg, "_zone_dot": zone_dot}
    records = sorted(
        _zone_a(zone_dot, cfg, ptr_map)
        + _zone_cname(zone_dot, cfg, ptr_map)
        + _zone_dkim1(zone_dot, cfg, ptr_map)
        + _zone_mx(zone_dot, cfg, ptr_map)
        + _zone_spf1(zone_dot, cfg, ptr_map)
        + _zone_srv(zone_dot, cfg, ptr_map)
        + _zone_txt(zone_dot, cfg, ptr_map)
        + _zone_txt_json(zone_dot, self_state.get("txt_json", {}), ptr_map)
    )
    content = _newlines(*_zone_header(zone_dot, cfg), *records)
    return zone, content


def _net_ptr(zone_dot, cfg, ptr_map):
    cidr = cfg["cidr"]
    ptr = ptr_map.get(cidr, {})

    def make_ptr(ip_str):
        num = _address_to_host_key(cidr, ip_str)
        entry = ptr.get(ip_str, {"yes": [], "no": []})
        yes = entry.get("yes", [])
        no = entry.get("no", [])
        if not yes and not no:
            return None
        if not yes and len(no) == 1:
            yes = no
        if not yes and no:
            raise RuntimeError(f"{no}: no PTR records for {ip_str}")
        if len(yes) > 1:
            raise RuntimeError(f"{yes}: too many PTR records for {ip_str}")
        return f"{num} IN PTR {yes[0]}"

    return _map_host_addresses(cidr, make_ptr)


def _net(zone_label, net_cfg, common, ptr_map):
    zone = f"{zone_label}.in-addr.arpa"
    zone_dot = _dot(zone)
    if isinstance(net_cfg, str):
        cfg = {**common, "cidr": net_cfg, "_zone_dot": zone_dot}
    else:
        cfg = {**common, **net_cfg, "_zone_dot": zone_dot}
    content = _newlines(*_zone_header(zone_dot, cfg), *_net_ptr(zone_dot, cfg, ptr_map))
    return zone, content


def _conf_zones(cfg):
    zone_names = (
        [f"{k}.in-addr.arpa" for k in sorted(cfg.get("nets", {}))]
        + sorted(cfg.get("zones", {}))
    )
    blocks = []
    for name in zone_names:
        blocks.append(
            f'zone "{name}" in {{\n  type master;\n  file "{name}";\n}};\n'
        )
    return "".join(blocks)


def _conf(cfg):
    header = (
        f'options {{\n'
        f'  directory "/{ZONE_DIR}";\n'
        f'  allow-transfer {{ none; }};\n'
        f'  query-source address * port 53;\n'
        f'  recursion no;\n'
        f'  version "n/a";\n'
        f'}};\n'
        f'logging {{\n'
        f'  category lame-servers {{ null; }};\n'
        f'}};\n'
        f'zone "." in {{\n'
        f'  type hint;\n'
        f'  file "{ROOT_FILE}";\n'
        f'}};\n'
    )
    return header + _conf_zones(cfg)


def _local_cfg(cfg):
    common = {
        "expiry": "1D",
        "hostmaster": "hostmaster.local.",
        "servers": ["local."],
        "minimum": "1D",
        "mx": None,
        "refresh": "1D",
        "retry": "1D",
        "spf1": None,
        "ttl": "1D",
    }
    net = "127.0.0.0/31"
    cfg.setdefault("nets", {})["0.0.127"] = {**common, "cidr": net}
    cfg.setdefault("zones", {})["local"] = {
        **common,
        "ipv4": {
            net: {
                1: [["@", {"mx": None, "spf1": None, "ptr": True}]],
            }
        },
    }


def _txt_json_parse(paths):
    res = {}
    for path in paths:
        with open(path) as f:
            data = json.load(f)
        for domain, subdomains in data.items():
            entries = res.setdefault(domain, [])
            if isinstance(subdomains, dict):
                for sub, txt in subdomains.items():
                    entries.append([sub, txt])
            else:
                entries.extend(subdomains)
    return res


def _write(files):
    for name, content in files.items():
        path = Path(name) if "/" in name else ZONE_DIR / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def root_file():
    import requests
    return requests.get(INTERNIC_ROOT_URL).text


def generate(cfg, txt_json_paths=None):
    self_state = {
        "txt_json": _txt_json_parse(txt_json_paths or []),
    }

    _local_cfg(cfg)
    Path("etc").mkdir(parents=True, exist_ok=True)
    ZONE_DIR.mkdir(parents=True, exist_ok=True)

    cfg["serial"] = _serial(cfg)

    zones = cfg.pop("zones", {})
    nets = cfg.pop("nets", {})
    ptr_map = {}

    zone_files = {}
    for zone_name in sorted(zones):
        name, content = _zone(self_state, zone_name, zones[zone_name], cfg, ptr_map)
        zone_files[name] = content

    for net_label in sorted(nets):
        name, content = _net(net_label, nets[net_label], cfg, ptr_map)
        zone_files[name] = content

    _write({
        "etc/named.conf": _conf({**cfg, "zones": zones, "nets": nets}),
        ROOT_FILE: root_file(),
        **zone_files,
    })


def _load_config(path):
    import runpy
    if path.endswith(".json"):
        with open(path) as f:
            return json.load(f)
    ns = runpy.run_path(path)
    return ns["RESULT"]


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(__doc__)
        sys.exit(1)

    cmd = argv[0]

    if cmd == "root_file":
        print(root_file(), end="")

    elif cmd == "generate":
        txt_json_paths = argv[1:]
        import runpy, tempfile
        raw = sys.stdin.read().strip()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(f"RESULT = {raw}\n")
            tmp_path = f.name
        try:
            ns = runpy.run_path(tmp_path)
            cfg = ns["RESULT"]
        finally:
            os.unlink(tmp_path)
        generate(cfg, txt_json_paths)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
