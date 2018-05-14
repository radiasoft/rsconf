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


_SCRIPTS = pkio.py_path('/etc/sysconfig/network-scripts')
_RESOLV_CONF = pkio.py_path('/etc/resolv.conf')
_IPTABLES = pkio.py_path('/etc/sysconfig/iptables')


def update_j2_ctx(j2_ctx):
    j2_ctx.network.trusted_nets = sorted(j2_ctx.network.trusted.keys())


class T(component.T):

    def internal_build(self):
        self.buildt.require_component('base_os')
        if not self.hdb.network.devices:
            # no devices, no network config
            self.append_root_bash(': nothing to do')
            return
        self.service_prepare((_SCRIPTS, _RESOLV_CONF))
        j2_ctx = self.hdb.j2_ctx_copy()
        update_j2_ctx(j2_ctx)
        self.install_access(mode='444', owner=self.hdb.rsconf_db.root_u)
        devs, defroute = self._devices(j2_ctx)
        if defroute:
            assert defroute.net.search and defroute.net.nameservers, \
                '{}: defroute needs search and nameservers'.format(defroute.net)
            self.install_resource('network/resolv.conf', j2_ctx, _RESOLV_CONF)
        z = j2_ctx.network
        if z.get('iptables_enable', False) and len(devs) == 1:
            z.update(
                inet_dev=defroute,
                private_devs=['lo'],
            )
        else:
            z.update(
                inet_dev=defroute if defroute.net.name.is_global else None,
            )
            z.setdefault(
                'private_devs',
                ['lo'] + [d.name for d in devs if d.net.name.is_private],
            )
            # No public addresses, no iptables
            z.setdefault('iptables_enable', bool(z.inet_dev))
        if z.iptables_enable:
            # Only restart iptables service if we have iptables
            self.service_prepare((_IPTABLES, _SCRIPTS), name='iptables')
        if z.inet_dev:
            self.hdb.network.primary_public_ip = z.inet_dev.ip
        self._write_files(j2_ctx, devs)

    def _defroute(self, routes):
        defroute = None
        for r in sorted(routes, key=lambda x: x.name):
            if not defroute:
                defroute = r
                continue
            dig = defroute.net.name.is_global
            rig = r.net.name.is_global
            if dig == rig:
                assert not dig, \
                    '{} & {}: are both global routes'.format(defroute.name, r.name)
                # unlikely case: defaults to the lowest non-global network route
            if rig:
                defroute = r
        return defroute

    def _devices(self, j2_ctx):
        z = j2_ctx.network
        self.__trusted_nets = self._nets(j2_ctx, z.trusted)
        j2_ctx.network.setdefault(
            'trusted_public_nets',
            sorted([n.name for n in self.__trusted_nets.values() if n.name.is_global]),
        )
        self.__untrusted_nets = self._nets(j2_ctx, z.untrusted)
        devs = []
        routes = []
        defroute = None
        j2_ctx.network.natted_dev = None
        for dn in sorted(j2_ctx.network.devices):
            d = copy.deepcopy(j2_ctx.network.devices[dn])
            devs.append(d)
            d.name = dn
            d.vlan = '.' in dn
            d.net = self._net_check(d.ip)
            if d.net.gateway:
                routes.append(d)
            if d.setdefault('defroute', False):
                assert not defroute, \
                    '{} & {}: both declared as default routes'.format(d, defroute)
                defroute = d
            if d.setdefault('is_natted', False):
                assert not j2_ctx.network.natted_dev, \
                    '{}: duplicate natted dev ({})'.format(
                        d.name,
                        j2_ctx.network.natted_dev.name,
                    )
                j2_ctx.network.natted_dev = d
        if not defroute:
            defroute = self._defroute(routes)
        defroute.defroute = True
        j2_ctx.network.defroute = defroute
        return devs, defroute

    def _nets(self, j2_ctx, spec):
        nets = pkcollections.Dict()
        for n, v in spec.items():
            v = copy.deepcopy(v)
            # Avoid this error:
            # Did you pass in a bytes (str in Python 2) instead of a unicode object?
            n = ipaddress.ip_network(pkcompat.locale_str(n))
            v.name = n
            v.ip = str(n.network_address)
            v.netmask = str(n.netmask)
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
        nip = ipaddress.ip_network(ip + '/32')
        #TODO(robnagler) untrusted networks are supernets of potentially trusted_nets
        # the only reason to add them is to find them for devices
        for nets in self.__untrusted_nets, self.__trusted_nets:
            for n in nets:
                if nip.subnet_of(n):
                    return nets[n]
        raise AssertionError('{}: ip not found in network.trusted'.format(nip))

    def _write_files(self, j2_ctx, devs):
        # Only for jupyterhub, explicitly set, and not on a machine
        # with a public address
        for d in devs:
            for k, v in d.items():
                if isinstance(v, bool):
                    d[k] = 'yes' if v else 'no'
            j2_ctx.network.dev = d
            self.install_resource(
                'network/ifcfg-en',
                j2_ctx,
                _SCRIPTS.join('ifcfg-' + d.name)
            )
        if j2_ctx.network.iptables_enable:
            assert not j2_ctx.docker.iptables, \
                '{}: docker.iptables not allowed on a public ip'.format(
                    j2_ctx.network.defroute.ip,
                )
            self.install_resource('network/iptables', j2_ctx, _IPTABLES)
        self.append_root_bash_with_main(j2_ctx)
