# -*- coding: utf-8 -*-
"""create nfs server config

:copyright: Copyright (c) 2018 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern import pkio
from pykern.pkdebug import pkdp
from rsconf import component

_EXPORTS_D = pkio.py_path("/etc/exports.d")
_SYSCONFIG_NFS = pkio.py_path("/etc/sysconfig/nfs")
_OPTIONS = "rw,no_root_squash,no_subtree_check,async,secure"


class T(component.T):
    def internal_build_compile(self):
        self.buildt.require_component("base_all")

        # Must be first to ensure /etc/exports.d exists
        jc = self.j2_ctx = self.hdb.j2_ctx_copy()
        z = jc.nfs_server
        if self.hdb.rsconf_db.is_centos7:
            z.conf_f = pkio.py_path("/etc/sysconfig/nfs")
        else:
            z.conf_f = pkio.py_path("/etc/nfs.conf.d/99-rsconf.conf")

    def internal_build_write(self):
        jc = self.j2_ctx
        z = jc.nfs_server
        self.append_root_bash("rsconf_yum_install nfs-utils")
        # Don't use "nfs", because "systemctl is-active nfs" returns unknown, b/c
        # nfs is a symlink to nfs-server.
        self.service_prepare((_EXPORTS_D, _SYSCONFIG_NFS), name="nfs-server")
        self.install_access(mode="400", owner=self.hdb.rsconf_db.root_u)
        for fs, clients in z.exports.items():
            z.client_args = " ".join(["{}({})".format(c, _OPTIONS) for c in clients])
            z.fs = fs
            # /foo/bar => foo_bar.exports
            f = fs[1:].replace("/", "_") + ".exports"
            self.install_resource("nfs_server/exports", jc, _EXPORTS_D.join(f))
        if self.hdb.rsconf_db.is_centos7:
            x = "RPCNFSDCOUNT={}".format(z.num_servers)
            self.rsconf_edit(
                z.conf_f,
                "^{}$".format(x),
                r"s<^#?\s*RPCNFSDCOUNT.*><{}>".format(x),
            )
            self.rsconf_service_restart()
        else:
            self.install_resource2(
                "nfs_server.conf",
                z.conf_f.dirpath(),
                host_f=z.conf_f.basename,
                access="400",
                host_d_access=PKDict(mode="700", owner=self.hdb.rsconf_db.root_u),
            )
