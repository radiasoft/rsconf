# -*- coding: utf-8 -*-
"""Sirepo development in a docker container on a remote machine

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkio
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
import subprocess


class T(component.T):
    def install_resource(self, *args, **kwargs):
        super().install_resource(*args, module_name="devbox", **kwargs)

    def internal_build_compile(self):
        from rsconf import systemd

        if self.name == "devbox":
            for u in self.hdb.devbox.users.keys():
                t = T(u, self.buildt)
                self.buildt.build_component(t)
            return
        self.buildt.require_component("docker", "network")
        jc, _ = self.j2_ctx_init()
        z = jc.devbox
        z.setdefault("volumes", {})
        # TODO(e-carlin): Better way then building the path manually
        # /srv/<component-name> is output by systemd.docker_unit_prepare
        # below but to call that we need z.host.ssh_d. z.host needs z.host_d
        # so we are in a dependency cycle
        z.host_d = systemd.unit_run_d(jc, self.name)
        z.secrets = self._gen_keys(jc, z)
        for x in "guest", "host":
            z[x] = self._gen_paths(z, z[x + "_d"])
        z.run_u = jc.rsconf_db.run_u
        # Only additional config for the server is the sshd config.
        z.run_d = systemd.docker_unit_prepare(self, jc, watch_files=[z.host.ssh_d])
        self._network(jc, z)

    def internal_build_write(self):
        from rsconf import systemd

        if self.name == "devbox":
            self.append_root_bash(": nothing to do")
            return
        jc = self.j2_ctx
        z = jc.devbox
        v = []
        x = [
            [z.host.ssh_d, z.guest.ssh_d],
            # SECURITY: no modifications to run_d
            [z.run_d, z.run_d, "ro"],
        ]
        for d in z.volumes:
            h = z.host[d]
            x.append([h, z.guest[d]])
            v.append(h)
        systemd.docker_unit_enable(
            self,
            jc,
            image=jc.devbox.docker_image,
            volumes=x,
            cmd="/usr/sbin/sshd -D -f '{}'".format(z.guest.sshd_config),
        )
        self.install_access(mode="700", owner=z.run_u)
        for d in [z.host_d, z.host.ssh_d, *v]:
            self.install_directory(d)
        self.install_access(mode="400")
        self.install_resource(z.host.sshd_config, jc)
        for k, v in z.secrets.items():
            self.install_abspath(v, z.host[k])

    def _network(self, jc, z):
        n = self.buildt.get_component("network")
        z.ip, _ = n.ip_and_net_for_host(jc.rsconf_db.host)
        z.ssh_port = jc.devbox.users[self.name]

    def _gen_keys(self, jc, z):
        from rsconf import db

        res = PKDict()
        b = db.secret_path(
            jc,
            "devbox/" + self.name,
            visibility="channel",
        )
        pkio.mkdir_parent(b)
        res.host_key_f = b.join("host_key")
        res.host_key_pub_f = res.host_key_f + ".pub"
        res.identity_f = b.join("identity")
        res.identity_pub_f = b.join("identity") + ".pub"
        for f in res.host_key_f, res.identity_f:
            if f.exists():
                continue
            subprocess.check_call(
                [
                    "ssh-keygen",
                    "-q",
                    "-t",
                    "ed25519",
                    "-N",
                    z.user_passwords[self.name],
                    "-C",
                    jc.rsconf_db.host,
                    "-f",
                    str(f),
                ],
                stderr=subprocess.STDOUT,
                shell=False,
            )
        return res

    def _gen_paths(self, z, db_d):
        res = PKDict()
        s = db_d.join(".ssh")
        res.ssh_d = s
        res.sshd_config = s.join("sshd_config")
        for k, v in z.secrets.items():
            res[k] = s.join(v.basename)
        for v in z.volumes:
            res[v] = db_d.join(v)
        return res
