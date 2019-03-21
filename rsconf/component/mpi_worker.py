# -*- coding: utf-8 -*-
u"""mpi worker daemon

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function


class T(component.T):
    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('docker')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.mpi_worker
        z.run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.run_u = j2_ctx.rsconf_db.run_u
        self._prepare_hosts()
        nc = self.buildt.get_component('network')
        for h in myhosts:
            ip, net = nc.ip_and_net_for_host(j2_ctx)
            z.mpi_slots consistent for cluster

    def internal_build_write(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        jc = self.j2_ctx
        z = jc.mpi_worker
        nc = self.buildt.get_component('network')
        systemd.custom_unit_enable(
            self,
            jc,
            run_u=z.run_u,
            run_group=z.run_group,
            run_d_mode='710',
        )
        # runtime_d (/run) set by custom_unit_enable
        z.stats_f = jc.systemd.runtime_d.join('bind.stats')
        z.session_key_f = jc.systemd.runtime_d.join('session.key')
        self.install_access(mode='750', owner=z.run_u, group=z.run_group)
        self.install_directory(z.db_d)
        self.install_access(mode='440')
        self.install_resource('bivio_named/named.conf', jc, z.conf_f)

        volumes =[
            $host_d $start_guest_d
        ]
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            env=env,
            volumes=volumes,
            cmd=/usr/sbin/sshd -D -f "$worker_guest_d/sshd_config"
        )

     ssh_file
        cat >> "$conf_d"/ssh_config <<EOF
Host $ip
    Port $start_ssh_port
    IdentityFile $worker_guest_d/id_ed25519
EOF
        cat >> "$conf_d"/known_hosts <<EOF
[$ip]:$start_ssh_port $worker_pub
EOF
