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
_IPTABLES = pkio.py_path('/etc/sysconf/iptables')


def update_j2_ctx(j2_ctx):
    j2_ctx.network.trusted_keys = sorted(j2_ctx.network.trusted.keys())


class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('base_os')
        if not self.hdb.network.devices:
            # no devices, no network config
            return
        systemd.unit_prepare(self, _SCRIPTS, _RESOLV_CONF, _IPTABLES)
        j2_ctx = self.hdb.j2_ctx_copy()
        self.install_access(mode='444', owner=self.hdb.rsconf_db.root_u)
        nets, net_check = _nets(j2_ctx)
        devs = []
        routes = []
        defroute = None
        for dn in sorted(j2_ctx.network.devices):
            d = copy.deepcopy(j2_ctx.network.devices[dn])
            devs.append(d)
            d.name = dn
            d.vlan = '.' in dn
            d.net = net_check(d.ip)
            if d.net.gateway:
                routes.append(d)
            if d.setdefault('defroute', False):
                assert not defroute, \
                    '{} & {}: both declared as default routes'.format(d, defroute)
                defroute = d
        if not defroute:
            defroute = _defroute(routes)
        if defroute:
            defroute.defroute = True
        j2_ctx.network.defroute = defroute
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
        if defroute:
            assert defroute.net.search and defroute.net.nameservers, \
                '{}: defroute needs search and nameservers'.format(defroute.net)
            self.install_resource('network/resolv.conf', j2_ctx, _RESOLV_CONF)
        self.append_root_bash_with_resource(
            'network/main.sh',
            j2_ctx,
            'network',
        )


def _defroute(routes):
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


def _nets(j2_ctx):
    nets = pkcollections.Dict()

    #TODO(robnagler) sanity check nets don't overlap?
    def net_check(ip):
        nip = ipaddress.ip_network(ip + '/32')
        for n in nets:
            if nip.subnet_of(n):
                return nets[n]
        raise AssertionError('{}: ip not found in network.trusted'.format(nip))

    for n, v in j2_ctx.network.trusted.items():
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
    return nets, net_check
