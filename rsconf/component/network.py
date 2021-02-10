# -*- coding: utf-8 -*-
u"""create network config

We disable NetworkManager, because we are managing the network now.
It's unnecessary complexity. NetworkManager (NM) create
``network-scripts`` files.

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections
from pykern.pkdebug import pkdp
from pykern import pkio
from pykern import pkcompat
import copy
import ipaddress
import socket


_SCRIPTS = pkio.py_path('/etc/sysconfig/network-scripts')
_RESOLV_CONF = pkio.py_path('/etc/resolv.conf')
_IPTABLES = pkio.py_path('/etc/sysconfig/iptables')


class T(component.T):

    def add_public_tcp_ports(self, ports):
        self._add_ports('public_tcp_ports', ports)

    def add_public_udp_ports(self, ports):
        self._add_ports('public_udp_ports', ports)

    def add_trusted_tcp_ports(self, ports):
        self._add_ports('trusted_tcp_ports', ports)

    def ip_and_net_for_host(self, host):
        ip = socket.gethostbyname(host)
        return ip, self._net_check(ip)

    def internal_build_compile(self):
        self.buildt.require_component('base_os')
        self.j2_ctx = self.hdb.j2_ctx_copy()
        jc = self.j2_ctx
        z = jc.network
        z.trusted_nets = tuple(sorted(z.trusted.keys()))
        z.pksetdefault(
            blacklist=[],
            public_tcp_ports=[],
            trusted_tcp_ports=[],
            public_udp_ports=[],
            pci_scanner_net=None,
        )
        self.__trusted_nets = self._nets(jc, z.trusted)
        z.blacklist = [str(ipaddress.ip_network(n)) for n in z.blacklist]
        z.setdefault(
            'trusted_public_nets',
            sorted([n.name for n in self.__trusted_nets.values() if n.is_global]),
        )
        self.__untrusted_nets = self._nets(jc, z.untrusted)
        if not self.hdb.network.devices:
            return
        self.service_prepare((_SCRIPTS, _RESOLV_CONF))
        self._devices(jc)
        if z.defroute:
            assert z.defroute.net.search and z.defroute.net.nameservers, \
                '{}: defroute needs search and nameservers'.format(z.defroute.net)
        z.pksetdefault(public_ssh_ports=[])
        if z.get('iptables_enable', False) and len(z._devs) == 1:
            z.update(
                inet_dev=z.defroute,
                private_devs=['lo'],
            )
        else:
            z.update(
                inet_dev=z.defroute if z.defroute.net.is_global else None,
            )
            z.setdefault(
                'private_devs',
                ['lo'] + [d.name for d in z._devs if d.net.is_private],
            )
            # No public addresses, no iptables
            z.setdefault('iptables_enable', bool(z.inet_dev))
        if z.iptables_enable:
            # Only restart iptables service if we have iptables
            self.service_prepare((_IPTABLES, _SCRIPTS), name='iptables')
        if z.inet_dev:
            #TODO(robnagler) update other uses and remove self.hdb mod
            z.primary_public_ip = z.inet_dev.ip
            self.hdb.network.primary_public_ip = z.inet_dev.ip
            if z.nat_input_dev:
                assert z.get('nat_output_dev'), \
                    'nat_input_dev and nat_output_dev both have to be defined'

    def internal_build_write(self):
        jc = self.j2_ctx
        jc = self.j2_ctx
        z = jc.network
        if not '_devs' in z:
            # no devices, no network config
            self.append_root_bash(': nothing to do')
            return
        for w in 'public_tcp_ports', 'public_udp_ports', 'trusted_tcp_ports':
            # some ports are listed as https and http, and others 9999
            z[w] = sorted([str(p) for p in z[w]])
        # Only for jupyterhub, explicitly set, and not on a machine
        # with a public address
        self.install_access(mode='444', owner=self.hdb.rsconf_db.root_u)
        if z.defroute:
            self.install_resource('network/resolv.conf', jc, _RESOLV_CONF)
        for d in z._devs:
            for k, v in d.items():
                if isinstance(v, bool):
                    d[k] = 'yes' if v else 'no'
            z.dev = d
            self.install_resource(
                'network/ifcfg-en',
                jc,
                _SCRIPTS.join('ifcfg-' + d.name)
            )
        if z.iptables_enable:
            assert not jc.docker.iptables, \
                '{}: docker.iptables not allowed on a public ip'.format(
                    z.defroute.ip,
                )
            self.install_resource('network/iptables', jc, _IPTABLES)
        self.append_root_bash_with_main(jc)

    def trusted_nets(self):
        return self.j2_ctx.network.trusted_nets

    def unchecked_public_ip(self):
        jc = self.j2_ctx
        if jc.network.get('inet_dev'):
            return jc.network.primary_public_ip
        return None

    def _add_ports(self, which, ports):
        assert len(ports[0]) > 2, \
            'invalid ports: {}'.format(ports)
        z = self.j2_ctx.network
        check = ('trusted_tcp_ports', 'public_tcp_ports') if 'tcp' in which \
            else ('public_udp_ports',)
        for p in ports:
            for w in check:
                assert not p in z[w], \
                    'port {} already in {}'.format(p, w)
            z[which].append(p)

    def _defroute(self, routes):
        defroute = None
        for r in sorted(routes, key=lambda x: x.name):
            if not defroute:
                defroute = r
                continue
            dig = defroute.net.is_global
            rig = r.net.is_global
            if dig == rig:
                assert not dig, \
                    '{} & {}: are both global routes'.format(defroute.name, r.name)
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
            d.vlan = '.' in dn
            d.net = self._net_check(d.ip)
            if d.net.gateway:
                routes.append(d)
            if d.setdefault('defroute', False):
                assert not z.defroute, \
                    '{} & {}: both declared as default routes'.format(d, z.defroute)
                z.defroute = d
            for x in 'input', 'output':
                if d.setdefault('is_nat_' + x, False):
                    ad = 'nat_{}_dev'.format(x)
                    assert not z.get(ad), \
                        '{}: duplicate {} ({})'.format(ad, d.name, z.get('ad').name)
                    z[ad] = d
        if not z.defroute:
            z.defroute = self._defroute(routes)
        z.defroute.defroute = True

    def _nets(self, jc, spec):
        nets = pkcollections.Dict()
        for n, v in spec.items():
            v = copy.deepcopy(v)
            # Avoid this error:
            # Did you pass in a bytes (str in Python 2) instead of a unicode object?
            n = ipaddress.ip_network(pkcompat.locale_str(n))
            v.name = n
            v.ip = str(n.network_address)
            v.netmask = str(n.netmask)
            # only needed for debugging
            v.setdefault('is_global', n.is_global)
            v.setdefault('is_private', not v.is_global and n.is_private)
            g = v.setdefault('gateway', '')
            if g:
                assert ipaddress.ip_network(pkcompat.locale_str(g + '/32')).subnet_of(n), \
                    '{}: gateway is not subnet of {}'.format(g, n)
            if 'nameservers' in v:
                v.nameservers = sorted([ipaddress.ip_address(x) for x in v.nameservers])
            nets[n] = v
        return nets

    #TODO(robnagler) sanity check nets don't overlap?
    def _net_check(self, ip):
        nip = ipaddress.ip_network(pkcompat.locale_str(ip + '/32'))
        #TODO(robnagler) untrusted networks are supernets of potentially trusted_nets
        # the only reason to add them is to find them for devices
        for nets in self.__untrusted_nets, self.__trusted_nets:
            for n in nets:
                if nip.subnet_of(n):
                    return nets[n]
        raise AssertionError('{}: ip not found in un/trusted_networks'.format(nip))
