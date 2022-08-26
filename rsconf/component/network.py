"""create network config

We disable NetworkManager, because we are managing the network now.
It's unnecessary complexity. NetworkManager (NM) create
``network-scripts`` files.

:copyright: Copyright (c) 2018-2022 RadiaSoft LLC.  All Rights Reserved.
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


class T(rsconf.component.T):
    def add_public_tcp_ports(self, ports):
        self._add_ports("public_tcp_ports", ports)

    def add_public_udp_ports(self, ports):
        self._add_ports("public_udp_ports", ports)

    def add_trusted_tcp_ports(self, ports):
        self._add_ports("trusted_tcp_ports", ports)

    def ip_and_net_for_host(self, host):
        ip = socket.gethostbyname(host)
        return ip, self._net_check(ip)

    def internal_build_compile(self):
        self.buildt.require_component("base_os")
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        z = jc.network
        z.trusted_nets = tuple(sorted(z.trusted.keys()))
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
        self.__trusted_nets = self._nets(jc, z.trusted)
        z.blocked_ips = [str(ipaddress.ip_network(n)) for n in z.blocked_ips]
        z.pksetdefault(
            trusted_public_nets=lambda: sorted(
                [n.name for n in self.__trusted_nets.values() if n.is_global]
            ),
        )
        self.__untrusted_nets = self._nets(jc, z.untrusted)
        if not self.hdb.network.devices:
            return
        self.service_prepare((_SCRIPTS, _RESOLV_CONF))
        self._devices(jc)
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
        if z.iptables_enable:
            # Only restart iptables service if we have iptables
            self.service_prepare((_IPTABLES, _SCRIPTS), name="iptables")
        if z.inet_dev:
            # TODO(robnagler) update other uses and remove self.hdb mod
            z.primary_public_ip = z.inet_dev.ip
            self.hdb.network.primary_public_ip = z.inet_dev.ip
            if z.nat_input_dev:
                assert z.get(
                    "nat_output_dev"
                ), "nat_input_dev and nat_output_dev both have to be defined"

    def internal_build_write(self):
        jc = self.j2_ctx
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
        if z.defroute:
            self.install_resource("network/resolv.conf", jc, _RESOLV_CONF)
        for d in z._devs:
            for k, v in d.items():
                if isinstance(v, bool):
                    d[k] = "yes" if v else "no"
            z.dev = d
            self.install_resource(
                "network/ifcfg-en", jc, _SCRIPTS.join("ifcfg-" + d.name)
            )
        if z.iptables_enable:
            assert (
                not jc.docker.iptables
            ), "{}: docker.iptables not allowed on a public ip".format(
                z.defroute.ip,
            )
            self.install_resource("network/iptables", jc, _IPTABLES)
        self.append_root_bash_with_main(jc)

    def trusted_nets(self):
        return self.j2_ctx.network.trusted_nets

    def unchecked_public_ip(self):
        jc = self.j2_ctx
        if jc.network.get("inet_dev"):
            return jc.network.primary_public_ip
        return None

    def _add_ports(self, which, ports):
        assert len(ports[0]) > 2, "invalid ports: {}".format(ports)
        z = self.j2_ctx.network
        c = (
            ("trusted_tcp_ports", "public_tcp_ports")
            if "tcp" in which
            else ("public_udp_ports",)
        )
        for p in ports:
            for w in c:
                assert not p in z[w], "port {} already in {}".format(p, w)
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

    def _devices(self, jc):
        z = jc.network
        z._devs = []
        routes = []
        z.defroute = None
        z.nat_input_dev = None
        for dn in sorted(z.devices):
            d = copy.deepcopy(z.devices[dn])
            z._devs.append(d)
            d.name = dn
            d.vlan = "." in dn
            d.net = self._net_check(d.ip)
            if d.net.gateway:
                routes.append(d)
            if d.setdefault("defroute", False):
                assert (
                    not z.defroute
                ), "{} & {}: both declared as default routes".format(d, z.defroute)
                z.defroute = d
            for x in "input", "output":
                if d.setdefault("is_nat_" + x, False):
                    ad = "nat_{}_dev".format(x)
                    assert not z.get(ad), "{}: duplicate {} ({})".format(
                        ad, d.name, z.get("ad").name
                    )
                    z[ad] = d
        if not z.defroute:
            z.defroute = self._defroute(routes)
        z.defroute.defroute = True

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
                assert ipaddress.ip_network(v.gateway + "/32",).subnet_of(
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
