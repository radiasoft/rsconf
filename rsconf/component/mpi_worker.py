# -*- coding: utf-8 -*-
u"""mpi worker daemon

:copyright: Copyright (c) 2019 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkdebug import pkdp
from pykern import pkcollections
from pykern import pkio
from rsconf import component
import subprocess


class T(component.T):
    def internal_build_compile(self):
        from rsconf import systemd

        # nfs_client is required, because host_d is likely on nfs
        self.buildt.require_component('docker', 'nfs_client', 'network')
        self.jc = self.hdb.j2_ctx_copy()
        jc = self.jc
        z = jc.mpi_worker
        self._find_cluster(jc, z)
        z.host_d = z.host_root_d.join(z.user)
        z.secrets = self._gen_keys(jc, z, jc.rsconf_db.host)
        for x in 'guest', 'host':
            z[x] = self._gen_paths(jc, z, z.get(x + '_d'))
        z.run_u = jc.rsconf_db.run_u
        z.run_d = systemd.docker_unit_prepare(self, jc, watch_files=[z.host_d])
        z.hosts_sorted = self._prepare_hosts(jc, z)

    def internal_build_write(self):
        from rsconf import systemd
        from rsconf.component import docker_registry

        jc = self.jc
        z = jc.mpi_worker
        self.install_access(mode='700', owner=z.run_u)
        # Need to make sure host_d exists, even though it isn't ours
        for d in z.host_d, z.host.conf_d, z.host.ssh_d:
            self.install_directory(d)
        self.install_access(mode='400')
        self.install_resource(z.host.sshd_config, jc)
        for k, v in z.secrets.items():
            self.install_abspath(v, z.host[k])
        if z.is_first:
            for f in 'ssh_config', 'known_hosts':
                self.install_resource(z.host[f], jc)
            self.install_access(mode='700')
            self.install_directory(z.host.bin_d)
            self.install_access(mode='500')
            self.install_resource(z.host.bin_d.join('rsmpi.sh'), jc)
        volumes = [[z.host_d, z.guest_d]]
        systemd.docker_unit_enable(
            self,
            jc,
            image=docker_registry.absolute_image(jc, z.docker_image),
            volumes=volumes,
            cmd="/usr/sbin/sshd -D -f '{}'".format(z.guest.sshd_config),
        )

    def _find_cluster(self, jc, z):
        h = jc.rsconf_db.host
        for u, hosts in z.clusters.items():
            if h in hosts:
                assert 'user' not in z, \
                    'host={} appears twice in clusters: {} and {}'.format(
                        h,
                        u,
                        z.user,
                    )
                z.update(
                    user=u,
                    hosts=hosts[:],
                    is_first=hosts[0] == h,
                )
        assert 'user' in z, \
            'host={} not found in clusters'.format(h)

    def _gen_keys(self, jc, z, host):
        from rsconf import db

        res = pkcollections.Dict()
        b = db.secret_path(
            jc,
            self.name + '_' + z.user,
            visibility='host',
            qualifier=host,
        )
        pkio.mkdir_parent(b)
        res.host_key_f = b.join('host_key')
        res.host_key_pub_f = res.host_key_f + '.pub'
        res.identity_f = b.join('identity')
        res.identity_pub_f = b.join('identity') + '.pub'
        for f in res.host_key_f, res.identity_f:
            if f.exists():
                continue
            subprocess.check_call(
                [
                    'ssh-keygen',
                    '-q',
                    '-t',
                    'ed25519',
                    '-N',
                    '',
                    '-C',
                    jc.rsconf_db.host,
                    '-f',
                    str(f),
                ],
                stderr=subprocess.STDOUT,
                shell=False,
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
        res.sshd_config = d.join('sshd_config')
        for k, v in z.secrets.items():
            res[k] = d.join(v.basename)
        return res

    def _prepare_hosts(self, jc, z):
        nc = self.buildt.get_component('network')
        z.ip, _ = nc.ip_and_net_for_host(jc.rsconf_db.host)
        if not z.is_first:
            return
        res = []
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
                    # replace this (first) host with current host (h) so we don't
                    # have to recompute
                    identity_f=pkio.py_path(
                        str(z.guest.identity_f).replace(jc.rsconf_db.host, h),
                    )
                ),
            )
        z.max_slots = z.slots_per_host * len(res)
        return sorted(res, key=lambda x: x.ip)
