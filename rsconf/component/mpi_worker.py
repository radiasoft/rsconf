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
        jc = self.hdb.j2_ctx_copy()
        z = jc.mpi_worker
        self._find_rank(jc, z)
        z.host_d = z.host_root_d.join(z.user)
        z.secrets = self._gen_keys(jc, z, jc.rsconf_db.host)
        for x in 'guest', 'host':
            z[x] = self._gen_paths(jc, z, z.get(where + '_d'))
        z.run_u = jc.rsconf_db.run_u
        z.run_d = systemd.docker_unit_prepare(self, jc, watch_files=[z.host_d])
        self._prepare_hosts(jc, z)

    def internal_build_write(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        jc = self.jc
        z = jc.mpi_worker
        self.install_access(mode='700', owner=z.run_u)
        for d in z.host_d, z.host.conf_d, z.host.ssh_d:
            self.install_directory(z.host_bin_d)
        self.install_access(mode='400')
        self.install_resource(
            self.name + '/' + z.host.sshd_config.basename,
            jc,
            z.host.sshd_config,
        )
        if z.is_first:
            self.install_resource(
                self.name + '/' + z.host.sshd_config.basename,
                jc,
                z.host.ssh_config,
            )
            self.install_resource(
                self.name + '/' + z.host.known_hosts.basename,
                jc,
                z.host.known_hosts,
            )
            self.install_directory(z.host.bin_d)
            self.install_access(mode='500')
            self.install_resource(
                self.name + '/rsmpi.sh',
                jc,
                z.host.bin_d.join('rsmpi'),
            )

        volumes =[
            $host_d $start_guest_d
        ]
        systemd.docker_unit_enable(
            self,
            jc,
            image=docker_registry.absolute_image(jc, z.docker_image),
            env=env,
            volumes=volumes,
            cmd=/usr/sbin/sshd -D -f "$worker_guest_d/sshd_config"
        )
        install files

    def _find_rank(self, jc, z):
        h = jc.rsconf_db.host
        for u, v in z.mpi_worker.users.items():
            if h in v:
                assert 'user' not in z, \
                    'host={} appears twice in users: {} and {}'.format(
                        h,
                        u,
                        z.my.user,
                    )
                z.update(
                    user=u,
                    hosts=v,
                    is_first=v[0] == h,
                )
        assert 'my' in my,
            'host={} not found in users'.format(h)

    def _gen_keys(self, jc, z, host):
        res = pkcollections.Dict()
        b = db.secret_path(
            jc,
            self.name + '_' + z.user,
            visibility='host',
            qualifier=host,
        )
        pkio.mkdir_parent_only(b)
        res.host_key_f = b.join('host_key')
        res.host_key_pub_f = res.host_key_f + '.pub'
        res.identity_f = b.join('identity')
        res.identity_pub_f = b.join('identity') + '.pub'
        for f in res.host_key_f, res.identity_f:
            if f.exists():
                continue
            subprocess.check_output(
                cmd,
                ['ssh-keygen', '-t', 'ed25519', '-q', '-N', '', host, '-f', f],
                stderr=subprocess.STDOUT,
            )
        return res

    def _gen_paths(self, jc, z, d):
        res = pkcollections.Dict()
        res.bin_d = d.join('bin')
        d = d.join('.rsmpi')
        res.conf_d = d
        res.known_hosts = d.join('known_hosts')
        res.ssh_config = d.join('ssh_config')
        d = d.join(jc.rsconf_db.host)
        res.ssh_d = d
        res['sshd_config'] = d.join('sshd_config')
        for k, v in z.secrets.items():
            res[k] = d.join(v.basename)

    def _prepare_hosts(self, jc, z):
        if not z.is_first:
            return
        res = []
        z.identities = pkcollections.Dict()
        z.net = None
        nc = self.buildt.get_component('network')
        for h in z.hosts:
            ip, net = nc.ip_and_net_for_host(h)
            if 'net' in z:
                assert net == z.net, \
                    'net={} for host={} not on same net={}'.format(
                        net,
                        h,
                        z.net,
                    )
            else:
                z.net = net
            s = self._gen_keys(jc, z, h)
            res.append(
                pkcollections.Dict(
                    host=h,
                    ip=ip,
                    host_key_pub=s.host_key_pub_f.read().rstrip(),
                    guest_identity_f=z.guest.identity_f.replace(jc.rsconf_db.host, h),
                ),
            )
        z.hosts_sorted = sorted(res, key=lambda x: x.h)
