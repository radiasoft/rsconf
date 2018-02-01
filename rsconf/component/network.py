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
from pykern import pkio

_NETWORK_SCRIPTS_D = pkio.py_path('/etc/sysconfig/network-scripts')
_RESOLV_CONF = pkio.py_path('/etc/resolv.conf')

class T(component.T):
    def internal_build(self):
        from rsconf.component import docker_registry

        self.buildt.require_component('base_os')
        j2_ctx = self.hdb.j2_ctx_copy()
        systemd.unit_prepare(self, _NETWORK_SCRIPTS_D)
        self.install_access(mode='400', owner=self.hdb.rsconf_db.root_u)
        for d in j2_ctx.network.devices:

        self.append_root_bash_with_resource(
            'network/main.sh',
            j2_ctx,
            'network_main',
        )

https://askubuntu.com/a/836155
#/etc/sysconfig/iptables
#/etc/sysconfig/network-scripts/ifcfg-<enet>1


ONBOOT=yes


DHCP:

https://serverfault.com/a/198694
Did they revert to APIPA addressing? 169.254.0.0/16? You can disable that with the
NOZEROCONF=Yes directive in /etc/sysconfig/network.

https://bugzilla.redhat.com/show_bug.cgi?id=234075
PERSISTENT_DHCLIENT="yes"

NM_CONTROLLED=no

https://www.thegeekdiary.com/centos-rhel-7-how-to-disable-networkmanager/amp/

PEERDNS=no
PEERROUTES=no
