# -*- coding: utf-8 -*-
u"""create base os configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from rsconf import component
from pykern import pkcollections

class T(component.T):
    def internal_build(self):
        self.install_access(mode='400', owner=self.hdb.rsconf_db_root_u)
        j2_ctx = pkcollections.Dict(self.hdb)
        self.install_resource(
            'base_os/60-rsconf-base.conf',
            j2_ctx,
            '/etc/sysctl.d/60-rsconf-base.conf',
        )
disk partitioning. may need to remove extra lv because have to add to create centos properly

        self.install_access(mode='444', owner=self.hdb.rsconf_db_root_u)
        self.install_resource('base_os/hostname', j2_ctx, '/etc/hostname')
        watch and update hostname? restart networking???
        self.append_root_bash_with_resource(
            'base_os/main.sh',
            j2_ctx,
            'base_os_main',
        )


'''
[root@localhost ~]# lvs
  LV     VG     Attr       LSize    Pool Origin Data%  Meta%  Move Log Cpy%Sync Convert
  home   centos -wi-ao----    5.00g
  remove centos -wi-ao---- <911.00g
  root   centos -wi-ao----    5.00g
  swap   centos -wi-ao----    4.00g
  var    centos -wi-ao----    5.00g
[root@localhost ~]# vi /etc/fstab
[root@localhost ~]# umount /remove
[root@localhost ~]# lvremove /dev/mapper/centos-remove
Do you really want to remove active logical volume centos/remove? [y/n]: y
  Logical volume "remove" successfully removed
  centos   1   4   0 wz--n- <930.00g <911.00g
'''
nfs client require yum install nfs-utils
