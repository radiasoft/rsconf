"""create network config

Network configuration supports both network-scripts (for CentOS 7) and NetworkManager
(for newer systems). The choice is made based on the OS version.

:copyright: Copyright (c) 2018-2024 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pykern import pkcollections
from pykern import pkcompat
from pykern import pkio
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
import rsconf
import copy
import ipaddress
import socket


_SCRIPTS = pkio.py_path("/etc/sysconfig/network-scripts")
_RESOLV_CONF = pkio.py_path("/etc/resolv.conf")
_IPTABLES = pkio.py_path("/etc/sysconfig/iptables")
_NM_CONNECTIONS = pkio.py_path("/etc/NetworkManager/system-connections")


class T(rsconf.component.T):
    def add_public_tcp_ports(self, ports):
        self._add_ports("public_tcp_ports", ports)

    def add_public_udp_ports(self, ports):
        self._add_ports("public_udp_ports", ports)

    def add_trusted_tcp_ports(self, ports):
        self._add_ports("trusted_tcp_ports", ports)

    def assert_host(self, host):
        try:
            if i := self.ip_and_net_for_host(host)[0]:
                return host
            m = f"unexpected gethostbyname ip={i}"
        except Exception as e:
            m = f"error={e}"
        raise ValueError(f"invalid host={host} {m}")

    def ip_and_net_for_host(self, host):
        ip = socket.gethostbyname(host)
        return ip, self._net_check(ip)

    def ip_for_this_host(self):
        return socket.gethostbyname(self.j2_ctx.rsconf_db.host)

    def internal_build_compile(self):
        def _init(z):
            z.pksetdefault(
                blocked_ips=[],
                drop_ssh_probes=True,
                pci_scanner_net=None,
                public_ssh_ports=[],
                public_tcp_ports=[],
                public_udp_ports=[],
                restricted_public_tcp_ports=PKDict,
                trusted_tcp_ports=[],
            )
            self.__trusted_nets = self._nets(self.j2_ctx, z.trusted)
            z.pkupdate(
                blocked_ips=tuple(str(ipaddress.ip_network(n)) for n in z.blocked_ips),
                trusted_nets=tuple(sorted(z.trusted.keys())),
                # TODO(robnagler) Generalize this check in db after #548 is merged
                use_network_manager=self.hdb.rsconf_db.host
                in self.hdb.get("alma_hosts", []),
            )
            z.pksetdefault(
                trusted_public_nets=lambda: sorted(
                    [n.name for n in self.__trusted_nets.values() if n.is_global]
                ),
            )
            self.__untrusted_nets = self._nets(self.j2_ctx, z.untrusted)

        def _inet_and_private_devs(z):
            if z.defroute:
                assert (
                    z.defroute.net.search and z.defroute.net.nameservers
                ), "{}: defroute needs search and nameservers".format(z.defroute.net)
            if z.get("iptables_enable", False) and len(z._devs) == 1:
                z.update(
                    inet_dev=z.defroute,
                    private_devs=["lo"],
                )
            else:
                z.update(
                    inet_dev=z.defroute if z.defroute.net.is_global else None,
                )
                z.pksetdefault(
                    private_devs=lambda: ["lo"]
                    + [d.name for d in z._devs if d.net.is_private],
                    # No public addresses, no iptables,
                    iptables_enable=lambda: bool(z.inet_dev),
                )

        def _iptables(device_dir, z):
            if not z.iptables_enable:
                return
            self.service_prepare((_IPTABLES, device_dir), name="iptables")

        def _public_ip(z):
            if not z.inet_dev:
                return
            # TODO(robnagler) update other uses and remove self.hdb mod
            z.primary_public_ip = z.inet_dev.ip
            self.hdb.network.primary_public_ip = z.inet_dev.ip
            if z.nat_input_dev and not z.get("nat_output_dev"):
                raise AssertionError(
                    "nat_input_dev and nat_output_dev both have to be defined"
                )

        def _service_and_iptables_watch_file(z):
            if z.use_network_manager:
                self.service_prepare((_NM_CONNECTIONS,), name="NetworkManager")
                z.main_function_calls = "network_manager_enable"
                return _NM_CONNECTIONS
            self.service_prepare((_SCRIPTS, _RESOLV_CONF))
            z.main_function_calls = "network_manager_disable"
            return _SCRIPTS

        self.buildt.require_component("base_os")
        _, z = self.j2_ctx_init()
        _init(z)
        if not z.devices:
            return
        w = _service_and_iptables_watch_file(z)
        self._devices()
        _inet_and_private_devs(z)
        _iptables(w, z)
        _public_ip(z)

    def internal_build_write(self):
        def _device(device, jc, z):
            for k, v in device.items():
                if isinstance(v, bool):
                    device[k] = "yes" if v else "no"
            # global state
            z.dev = device
            if z.use_network_manager:
                self.install_resource(
                    "network/nm-connection",
                    jc,
                    _NM_CONNECTIONS.join(device.name + ".nmconnection"),
                )
            else:
                self.install_resource(
                    "network/ifcfg-en", jc, _SCRIPTS.join("ifcfg-" + device.name)
                )
            z.pkdel("dev")

        jc = self.j2_ctx
        z = jc.network
        # Order matters: _restricted_public_tcp_ports modifed public_tcp_ports
        # to remove ports that that in the restricted set.
        self._restricted_public_tcp_ports(z)
        if not "_devs" in z:
            # no devices, no network config
            self.append_root_bash(": nothing to do")
            return
        for w in "public_tcp_ports", "public_udp_ports", "trusted_tcp_ports":
            # some ports are listed as https and http, and others 9999
            z[w] = sorted([str(p) for p in z[w]])
        # Only for jupyterhub, explicitly set, and not on a machine
        # with a public address
        self.install_access(mode="444", owner=self.hdb.rsconf_db.root_u)
        if z.defroute and not z.use_network_manager:
            self.install_resource("network/resolv.conf", jc, _RESOLV_CONF)
        if z.use_network_manager:
            # TODO(robnagler) does this have to be writable?
            self.install_access(mode="600", owner=self.hdb.rsconf_db.root_u)
        for d in z._devs:
            # destructive
            _device(copy.deepcopy(d), jc, z)
        if z.iptables_enable:
            assert (
                not jc.docker.iptables
            ), "{}: docker.iptables not allowed on a public ip".format(
                z.defroute.ip,
            )
            self.install_access(mode="444", owner=self.hdb.rsconf_db.root_u)
            self.install_resource("network/iptables", jc, _IPTABLES)
            z.main_function_calls += "; network_iptables_enable"
        self.append_root_bash_with_main(jc)

    def trusted_nets(self):
        return self.j2_ctx.network.trusted_nets

    def unchecked_public_ip(self):
        jc = self.j2_ctx
        if jc.network.get("inet_dev"):
            return jc.network.primary_public_ip
        return None

    def _add_ports(self, which, ports):
        z = self.j2_ctx.network
        c = (
            ("trusted_tcp_ports", "public_tcp_ports")
            if "tcp" in which
            else ("public_udp_ports",)
        )
        for p in ports:
            z[which].append(p)

    def _restricted_public_tcp_ports(self, z):
        if not z.restricted_public_tcp_ports:
            return
        assert (
            z.iptables_enable
        ), f"iptables must be configured for restricted_public_tcp_ports={z.restricted_public_tcp_ports}"
        r = PKDict()
        for k in sorted(z.restricted_public_tcp_ports.keys()):
            assert (
                k in z.public_tcp_ports
            ), f"restricted_public_tcp_ports={k} must be in public_tcp_ports"
            z.public_tcp_ports.remove(k)
            r[k] = sorted(
                str(self._net_or_ip(v)) for v in z.restricted_public_tcp_ports[k]
            )
        self.restricted_public_tcp_ports = r

    def _defroute(self, routes):
        defroute = None
        for r in sorted(routes, key=lambda x: x.name):
            if not defroute:
                defroute = r
                continue
            dig = defroute.net.is_global
            rig = r.net.is_global
            if dig == rig:
                assert not dig, "{} & {}: are both global routes".format(
                    defroute.name, r.name
                )
                # unlikely case: defaults to the lowest non-global network route
            if rig:
                defroute = r
        return defroute

    def _devices(self):
        def _init(name, z):
            d = copy.deepcopy(z.devices[name])
            if z.use_network_manager:
                d.nm = PKDict()
            z._devs.append(d)
            d.name = name
            return d

        def _nat(device, z):
            for x in "input", "output":
                if not device.setdefault("is_nat_" + x, False):
                    continue
                n = f"nat_{x}_dev"
                if z.get(n):
                    raise AssertionError(f"{n}: duplicate {device.name} ({z[n].name})")
                z[n] = device

        def _net(device, z):
            device.net = self._net_check(device.ip)
            if device.net.gateway:
                routes.append(device)
            if device.setdefault("defroute", False):
                if z.defroute:
                    raise AssertionError(
                        f"{defroute} & {z.defroute}: both declared as default routes"
                    )
                z.defroute = device

        def _nm_ipv4_vars(z):
            if not z.use_network_manager:
                return
            for d in z._devs:
                n = d.net if d.defroute else None
                d.nm.ipv4_never_default = not n
                (d.nm.ipv4_dns_search, d.nm.ipv4_dns) = (
                    (n.get("search", ""), ";".join(map(str, n.get("nameservers", ()))))
                    if n
                    else ("", "")
                )

        def _vlan(device):
            x = device.name.split(".")
            device.vlan = len(x) > 1
            if "nm" not in device:
                return
            device.nm.connection_type = "vlan" if device.vlan else "ethernet"
            (device.nm.vlan_parent, device.nm.vlan_id) = x if device.vlan else ("", "")

        z = self.j2_ctx.network
        z._devs = []
        routes = []
        z.defroute = None
        z.nat_input_dev = None
        for dn in sorted(z.devices):
            d = _init(dn, z)
            _net(d, z)
            _nat(d, z)
            _vlan(d)
        if not z.defroute:
            z.defroute = self._defroute(routes)
        z.defroute.defroute = True
        _nm_ipv4_vars(z)

    def _nets(self, jc, spec):
        nets = pkcollections.Dict()
        for n, v in spec.items():
            v = copy.deepcopy(v)
            n = ipaddress.ip_network(n)
            v.name = n
            v.ip = str(n.network_address)
            v.netmask = str(n.netmask)
            v.pksetdefault(
                # only needed for debugging
                gateway="",
                is_global=n.is_global,
            )
            v.pksetdefault(is_private=lambda: not v.is_global and n.is_private)
            if v.gateway:
                assert ipaddress.ip_network(
                    v.gateway + "/32",
                ).subnet_of(
                    n
                ), "{}: gateway is not subnet of {}".format(v.gateway, n)
            if "nameservers" in v:
                v.nameservers = sorted([ipaddress.ip_address(x) for x in v.nameservers])
            nets[n] = v
        return nets

    # TODO(robnagler) sanity check nets don't overlap?
    def _net_check(self, ip):
        nip = ipaddress.ip_network(ip + "/32")
        # TODO(robnagler) untrusted networks are supernets of potentially trusted_nets
        # the only reason to add them is to find them for devices
        for nets in self.__untrusted_nets, self.__trusted_nets:
            for n in nets:
                if nip.subnet_of(n):
                    return nets[n]
        raise AssertionError("{}: ip not found in un/trusted_networks".format(nip))

    def _net_or_ip(self, val):
        return ipaddress.ip_network(val) if "/" in val else ipaddress.ip_address(val)
