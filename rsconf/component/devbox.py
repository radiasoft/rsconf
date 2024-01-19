# -*- coding: utf-8 -*-
"""Sirepo development in a docker container on a remote machine

:copyright: Copyright (c) 2022 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern import pkconfig
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdp
from rsconf import component
import ipaddress

_RSIVIZ_DICE_NETWORK_DISCOVERY_PORT = 5556


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd

        def _create_user_instances():
            for u in self.hdb.devbox.users.keys():
                self.buildt.build_component(
                    T(
                        f"{self.module_name}_{u}",
                        self.buildt,
                        _user=u,
                        module_name=self.module_name,
                    )
                )

        if self._is_main_instance():
            _create_user_instances()
            return
        self.buildt.require_component("docker", "network")
        jc, z = self.j2_ctx_init()
        jc[self.module_name].setdefault("ssh_service_port_delta", 1000)
        z.setdefault("volumes", ["jupyter", "src"])
        z.host_d = systemd.unit_run_d(jc, self.name)
        self._gen_secrets(jc)
        z.guest = self._gen_paths(z, jc[self.module_name].guest_d, ".ssh")
        z.host = self._gen_paths(z, z.host_d, "sshd")
        z.run_u = jc.rsconf_db.run_u
        # Only additional config for the server is the sshd config.
        z.run_d = systemd.docker_unit_prepare(
            self,
            jc,
            watch_files=[z.host.ssh_d],
            docker_exec="/usr/sbin/sshd -e -D -f '{}'".format(
                z.guest.ssh_d.join("sshd_config"),
            ),
        )
        u = self._user_cfg(jc)
        z.docker_image = jc[self.module_name].docker_image
        if isinstance(u, PKDict):
            z.docker_image = u.get("docker_image", z.docker_image)
            z.ssh_port = u.ssh_port
        else:
            z.ssh_port = u
        self._network(jc, z)

    def internal_build_write(self):
        from rsconf import systemd

        if self._is_main_instance():
            self.append_root_bash(": user instances do all the installs")
            return
        jc = self.j2_ctx
        z = jc[self.name]
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
            image=z.docker_image,
            volumes=v,
        )
        j = None
        for d in map(lambda x: x[0], v):
            self.install_access(mode="700", owner=z.run_u)
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
            if "jupyter" in str(d):
                j = d.join("bashrc")
        self._jupyter_bashrc(jc, z, j)
        self.install_access(mode="400")
        self.install_resource(z.host.sshd_config, jc)
        for k, v in self.secrets.items():
            self.install_abspath(v, z.host[k])

    def _env(self, name, value, path):
        v = str(value)
        # TODO probably could recursively quote
        if "'" in v:
            raise ValueError(f"single quote in value={v} of bash variable name={name}")
        self.rsconf_append(
            path,
            f"export {name}='{v}'",
        )

    def _gen_paths(self, z, db_d, ssh_d):
        res = PKDict(ssh_d=db_d.join(ssh_d))
        res.pkupdate(sshd_config=res.ssh_d.join("sshd_config"))
        for e in z.volumes:
            res.pkupdate({e: db_d.join(e)})
        for k, v in self.secrets.items():
            res.pkupdate({k: res.ssh_d.join(v.basename)})
        return res

    def _gen_secrets(self, jc):
        s = super().gen_identity_and_host_ssh_keys(jc, "host", encrypt_identity=True)
        self.secrets = PKDict({k: s[k] for k in ("host_key_f", "identity_pub_f")})

    def _jupyter_bashrc(self, jc, z, path):
        self.install_access(mode="600")
        self.install_ensure_file_exists(path)
        for n in ("package_path", "sim_types"):
            if n in jc[self.module_name]:
                self._env(
                    f"SIREPO_FEATURE_CONFIG_{n.upper()}",
                    ":".join(jc[self.module_name][n]),
                    path,
                )
        z.service_port = z.ssh_port + jc[self.module_name].ssh_service_port_delta
        z.job_supervisor_port = (
            z.service_port + jc[self.module_name].ssh_service_port_delta
        )
        for n in ("service_port", "job_supervisor_port"):
            self._env(f"SIREPO_PKCLI_{n.upper()}", z[n], path)
        for n in ("DRIVER_LOCAL", "API"):
            self._env(
                f"SIREPO_JOB_{n}_SUPERVISOR_URI",
                f"http://127.0.0.1:{z.job_supervisor_port}",
                path,
            )
        self._rsiviz(jc, z, path)

    def _network(self, jc, z):
        n = self.buildt.get_component("network")
        z.ip = n.unchecked_public_ip() or n.ip_and_net_for_host(jc.rsconf_db.host)[0]
        n.add_public_tcp_ports([str(z.ssh_port)])

    def _rsiviz(self, jc, z, path):
        u = self._user_cfg(jc)
        if not isinstance(u, PKDict) or not "rsiviz" in u:
            return
        e = [
            ("PYKERN_PKASYNCIO_SERVER_PORT", u.rsiviz.port_base),
            (
                "RSIVIZ_PKCLI_SERVICE_DICE_NETWORK_CLUSTER_INTERFACE_ADDRESS",
                u.rsiviz.ip_base,
            ),
            (
                "RSIVIZ_PKCLI_SERVICE_DICE_NETWORK_DISCOVERY_ADDRESS",
                f"{u.rsiviz.ip_base}:{_RSIVIZ_DICE_NETWORK_DISCOVERY_PORT}",
            ),
            ("RSIVIZ_PKCLI_SERVICE_INDEX_IFRAME_PORT", u.rsiviz.port_base + 1),
        ]
        d = self.j2_ctx.pkunchecked_nested_get("rsiviz.dice")
        if d:
            e.extend(list(pkconfig.to_environ(["*"], PKDict(dice=d)).items()))
        for k, v in e:
            self._env(
                k,
                str(v),
                path,
            )

    def _user_cfg(self, jc):
        return jc[self.module_name].users[self._user]
