"""Generate named.conf and zone files

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
import datetime
import ipaddress
import pykern.pkjson
import os
import pykern.fconf
import pykern.pkcollections
import pykern.pkio
import re
import requests
import subprocess


INTERNIC_ROOT_URL = "https://www.internic.net/zones/named.root"

_GLOBAL_REPLACE = "GLOBAL"


def gen(root_dir, cfg_dir, out_dir=".", test_serial=None):
    """Generate named.conf and zone files in the current directory

    Args:
        root_dir (str): directory written to named.conf options.directory
        cfg_dir (str): directory containing .py and .yml fconf input files
        out_dir (str): where to write the output [.]
        test_serial (int): override SOA serial for testing [None]
    """
    d = pykern.pkio.py_path(cfg_dir)
    _gen(
        root_dir,
        pykern.fconf.parse_all(d),
        d,
        pykern.pkio.py_path(out_dir),
        int(test_serial) if test_serial is not None else None,
    )


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


def _cidr_hosts(cidr):
    return ipaddress.IPv4Network(cidr, strict=False)


def _conf(root_dir, root_file):
    return f"""options {{
  directory "{root_dir}";
  allow-transfer {{ none; }};
  recursion no;
  version "n/a";
}};
logging {{
  category lame-servers {{ null; }};
}};
include "zones.conf";
"""


def _zones_conf(root_file, cfg):
    zone_names = [
        f"{k}.in-addr.arpa" for k in sorted(cfg.get("nets", PKDict()))
    ] + sorted(cfg.get("zones", PKDict()))
    blocks = [f'zone "." in {{\n  type hint;\n  file "{root_file}";\n}};\n']
    for name in zone_names:
        blocks.append(f'zone "{name}" in {{\n  type primary;\n  file "{name}";\n}};\n')
    return "".join(blocks)


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


def _newlines(*parts):
    return "\n".join(parts) + "\n"


def _serial(cfg):
    def _check(curr, today):
        m = today + 99
        rv = curr + 1 if curr >= today else today
        if rv >= m:
            raise RuntimeError(f"too many updates today curr={curr} new={rv} max={m}")
        return rv

    def _dig():
        s = cfg.servers[0]
        return ["dig", "soa", s, "@" + s]

    o = subprocess.check_output(_dig(), text=True)
    for x in o.splitlines():
        if x.startswith(";"):
            continue
        if m := re.match(r"^\S+\s+\d+\s+IN\s+SOA\s+\S+\.\s+\S+\.\s+(\d{1,10})\s+\d", x):
            return _check(
                int(m.group(1)), int(datetime.date.today().strftime("%Y%m%d00"))
            )
    raise RuntimeError(f"could not find SOA cmd={_dig()} out={o}")


def _zone(zone, zone_cfg, common, ptr_map):
    def _dedup(recs):
        p = None
        for k in recs:
            if k == p:
                continue
            yield k
            p = k

    zone_dot = _dot(zone)
    cfg = PKDict({**common, **zone_cfg, "_zone_dot": zone_dot})
    records = sorted(
        _zone_a(zone_dot, cfg, ptr_map)
        + _zone_cname(zone_dot, cfg, ptr_map)
        + _zone_mx(zone_dot, cfg, ptr_map)
        + _zone_spf1(zone_dot, cfg, ptr_map)
        + _zone_srv(zone_dot, cfg, ptr_map)
        + _zone_txt(zone_dot, cfg, ptr_map)
        + _zone_txt_json(zone_dot, common.get("txt_json", PKDict()), ptr_map)
    )
    return zone, _newlines(*_zone_header(zone_dot, cfg), *_dedup(records))


def _zone_a(zone, cfg, ptr_map):
    def op(host, host_cfg, ip, cidr):
        entry = ptr_map.setdefault(cidr, PKDict()).setdefault(ip, {"yes": [], "no": []})
        key = "yes" if host_cfg.get("ptr") else "no"
        entry[key].append(_dot(host, zone))
        return f"{host} IN A {ip}"

    return _zone_ipv4_map(zone, cfg, ptr_map, op)


def _zone_cname(zone, cfg, ptr_map):
    return _zone_literal("cname", zone, cfg)


def _zone_header(zone_dot, cfg):

    def _records():
        return [f"@ IN NS {_dot(s, zone_dot)}" for s in cfg.servers]

    def _soa():
        s = _dot(cfg.servers[0], zone_dot.rstrip(".") + ".")
        h = _dot(cfg.hostmaster, zone_dot.rstrip(".") + ".")
        return f"@ IN SOA {s} {h} ( {cfg.serial} {cfg.refresh} {cfg.retry} {cfg.expiry} {cfg.minimum} )"

    return (f"$TTL {cfg.ttl}", f"$ORIGIN {zone_dot}", _soa(), *_records())


def _zone_ipv4_map(zone, cfg, ptr_map, op):

    def _normalize_host_entry(entry):
        if isinstance(entry, PKDict):
            if (host := entry.get("name")) is None:
                raise ValueError(f"missing name in entry={entry}")
            hcfg = entry
        elif isinstance(entry, str):
            host = entry
            hcfg = PKDict()
        else:
            raise ValueError(f"invalid entry={entry}")
        if isinstance(host, str) and re.match(r"^@(?=[\w@])", host):
            host = host[1:]
            hcfg["ptr"] = True
        merged = PKDict({**cfg, **hcfg})
        if host == "@":
            host = cfg.get("_zone_dot", "@")
        return [host, merged]

    def _process_ip(ip_str, cidr, host_map):
        key = _address_to_host_key(cidr, ip_str)
        hosts = host_map.get(key)
        if hosts is None:
            return None
        if not isinstance(hosts, list):
            hosts = [hosts]
        out = []
        for entry in sorted(
            [_normalize_host_entry(e) for e in hosts],
            key=lambda x: x[0],
        ):
            r = op(entry[0], entry[1], ip_str, cidr)
            if r is not None:
                if isinstance(r, list):
                    out.extend(r)
                else:
                    out.append(r)
        return out or None

    ipv4 = cfg.get("ipv4")
    if ipv4 is None:
        return []
    if not isinstance(ipv4, PKDict):
        raise ValueError(f"invalid input ipv4={ipv4}")
    results = []
    for cidr in sorted(ipv4):
        host_map = ipv4[cidr]
        net = ipaddress.IPv4Network(cidr, strict=False)
        results.extend(
            _map_host_addresses(cidr, lambda ip: _process_ip(ip, cidr, host_map))
        )
    return results


def _zone_ipv4_map_array(ipv4_list):
    res = PKDict()
    it = iter(ipv4_list)
    for key, val in zip(it, it):
        cidr, num = key
        cidr_dict = res.setdefault(cidr, PKDict())
        if num in cidr_dict:
            raise ValueError(f"Duplicate host cidr={cidr} num={num}")
        cidr_dict[num] = val
    return res


def _zone_literal(cfg_which, zone, cfg):
    def _pairs(values):
        for k, v in values.items() if isinstance(values, PKDict) else values:
            yield k, v

    values = cfg.get(cfg_which, PKDict())
    dns_type = cfg_which.upper()
    return [f"{host} IN {dns_type} {val}" for host, val in _pairs(values)]


def _zone_mx(zone, cfg, ptr_map):
    def op(host, host_cfg, ip, cidr):
        if (mx := host_cfg.get("mx")) is None:
            mx = host
        elif not mx:
            return None
        out = []
        for entry in mx if isinstance(mx, list) else [mx]:
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
        if (spf1 := host_cfg.get("spf1")) is None:
            spf1 = ""
        elif not spf1:
            return None
        spf1 = spf1.replace(_GLOBAL_REPLACE, cfg.get("spf1") or "")
        return f'{host} IN TXT "v=spf1 a mx {spf1} -all"'

    return _zone_ipv4_map(zone, cfg, ptr_map, op)


def _zone_srv(zone, cfg, ptr_map):
    return _zone_literal("srv", zone, cfg)


def _zone_txt(zone, cfg, ptr_map):
    return _zone_literal("txt", zone, cfg)


def _zone_txt_json(zone_dot, txt_json, ptr_map):
    zone_name = zone_dot.rstrip(".")
    records = txt_json.get(zone_name, [])
    return [f"{host} IN TXT {val}" for host, val in records]


def _net(zone_label, net_cfg, common, ptr_map):

    def _ptr(zone_dot, cfg, ptr_map):
        cidr = cfg["cidr"]
        ptr = ptr_map.get(cidr, PKDict())

        def make_ptr(ip_str):
            num = _address_to_host_key(cidr, ip_str)
            entry = ptr.get(ip_str, PKDict({"yes": [], "no": []}))
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

    zone = f"{zone_label}.in-addr.arpa"
    zone_dot = _dot(zone)
    if isinstance(net_cfg, str):
        cfg = PKDict({**common, "cidr": net_cfg, "_zone_dot": zone_dot})
    else:
        cfg = PKDict({**common, **net_cfg, "_zone_dot": zone_dot})
    content = _newlines(*_zone_header(zone_dot, cfg), *_ptr(zone_dot, cfg, ptr_map))
    return zone, content


def _local_cfg(cfg):
    common = PKDict(
        {
            "expiry": "1D",
            "hostmaster": "hostmaster.local.",
            "servers": ["local."],
            "minimum": "1D",
            "mx": "",
            "refresh": "1D",
            "retry": "1D",
            "spf1": "",
            "ttl": "1D",
        }
    )
    net = "127.0.0.0/31"
    cfg.setdefault("nets", PKDict())["0.0.127"] = PKDict({**common, "cidr": net})
    cfg.setdefault("zones", PKDict())["local"] = PKDict(
        {
            **common,
            "ipv4": PKDict(
                {
                    net: PKDict(
                        {
                            1: [PKDict(name="@", mx="", spf1="", ptr=True)],
                        }
                    ),
                }
            ),
        }
    )


def _txt_json_parse(paths):
    res = PKDict()
    for path in paths:
        data = pykern.pkjson.load_any(pykern.pkio.read_text(path))
        for domain, subdomains in data.items():
            entries = res.setdefault(domain, [])
            if isinstance(subdomains, dict):
                for sub, txt in subdomains.items():
                    entries.append([sub, txt])
            else:
                entries.extend(subdomains)
    return res


def _gen(root_dir, cfg, cfg_dir, out_dir, test_serial):
    def _root_file():
        return requests.get(INTERNIC_ROOT_URL).text

    def _test_serial(serial):
        if not test_serial:
            return serial
        if test_serial > serial:
            raise AssertionError(
                f"test_serial={test_serial} > computed serial={serial}"
            )
        return test_serial

    def _write(files):
        pykern.pkio.mkdir_parent(out_dir)
        for n, c in files.items():
            pykern.pkio.write_text(out_dir.join(n), c)

    _local_cfg(cfg)
    cfg.serial = _test_serial(_serial(cfg))
    cfg.txt_json = _txt_json_parse(pykern.pkio.sorted_glob(cfg_dir.join("*.json")))
    zones = cfg.pop("zones", PKDict())
    nets = cfg.pop("nets", PKDict())
    ptr_map = PKDict()
    zone_files = PKDict()
    for zone_name in sorted(zones):
        name, content = _zone(zone_name, zones[zone_name], cfg, ptr_map)
        zone_files[name] = content
    for net_label in sorted(nets):
        name, content = _net(net_label, nets[net_label], cfg, ptr_map)
        zone_files[name] = content
    n = "named.root"
    cfg.pkupdate(nets=nets, zones=zones)
    return _write(
        zone_files.pkupdate(
            {
                "named.conf": _conf(root_dir, n),
                "zones.conf": _zones_conf(n, cfg),
                n: _root_file(),
            }
        ),
    )
