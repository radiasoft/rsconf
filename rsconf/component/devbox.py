# -*- coding: utf-8 -*-
"""Sirepo development in a docker container on a remote machine

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component

_PASSWD_SECRET_JSON_F = "devbox_auth.json"


class T(component.T):
    def gen_host_and_identity_ssh_keys(self, jc):
        res = super().gen_host_and_identity_ssh_keys(
            jc, "host", password_filename=_PASSWD_SECRET_JSON_F
        )
        for k in list(res.keys()):
            if k not in ("host_key_f", "identity_pub_f"):
                res.pkdel(k)
        return res

    def internal_build_compile(self):
        from rsconf import systemd

        if "user_name" not in self:
            for u in self.hdb.devbox.users.keys():
                self.buildt.build_component(
                    T(
                        f"{self.name}_{u}",
                        self.buildt,
                        user_name=u,
                        module_name=self.name,
                    )
                )
            return
        self.buildt.require_component("docker", "network")
        jc, _ = self.j2_ctx_init()
        z = jc.devbox
        z.setdefault("volumes", ["jupyter", "src"])
        z.host_d = systemd.unit_run_d(jc, self.name)
        z.secrets = self.gen_host_and_identity_ssh_keys(jc)
        for x, d in ("guest", ".ssh"), ("host", "sshd"):
            z[x] = self._gen_paths(z, z[x + "_d"], d)
        z.run_u = jc.rsconf_db.run_u
        # Only additional config for the server is the sshd config.
        z.run_d = systemd.custom_unit_prepare(self, jc, watch_files=[z.host.ssh_d])
        self._network(jc, z)

    def internal_build_write(self):
        from rsconf import systemd

        if "user_name" not in self:
            self.append_root_bash(": user instances do all the installs")
            return
        jc = self.j2_ctx
        z = jc.devbox
        v = [[z.host[v], z.guest[v], "rw"] for v in z.volumes]
        v.extend(
            [
                # SECURITY: no modifications to run_d or ssh_d
                [z.host.ssh_d, z.guest.ssh_d, "ro"],
                [z.run_d, z.run_d, "ro"],
            ],
        )
        systemd.docker_unit_enable(
            self,
            jc,
            image=jc.devbox.docker_image,
            volumes=v,
            cmd="/usr/sbin/sshd -D -f '{}'".format(z.guest.ssh_d.join("sshd_config")),
        )
        self.install_access(mode="700", owner=z.run_u)
        for d in map(lambda x: x[0], v):
            self.install_directory(d)
            if "src" in str(d):
                r = ""
                p = d
                for c in ("biviosoftware", "home-env"):
                    p = p.join(c)
                    self.install_directory(p)
                    r += f"/{c}"
                self.append_root_bash(
                    f"rsconf_clone_repo https://github.com{r}.git {p} {jc.rsconf_db.run_u}"
                )
        self.install_access(mode="400")
        self.install_resource(z.host.sshd_config, jc)
        for k, v in z.secrets.items():
            self.install_abspath(v, z.host[k])

    def _gen_paths(self, z, db_d, ssh_d):
        res = PKDict(ssh_d=db_d.join(ssh_d))
        res.pkupdate(sshd_config=res.ssh_d.join("sshd_config"))
        for e in z.volumes:
            res.pkupdate({e: db_d.join(e)})
        for k, v in z.secrets.items():
            res.pkupdate({k: res.ssh_d.join(v.basename)})
        return res

    def _network(self, jc, z):
        n = self.buildt.get_component("network")
        z.ip, _ = n.ip_and_net_for_host(jc.rsconf_db.host)
        z.ssh_port = jc.devbox.users[self.user_name]
