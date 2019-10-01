# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkcollections
from pykern import pkconfig
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd
import base64
import os


_DB_SUBDIR = 'db'
#TODO(robnagler) import from sirepo directly
_USER_SUBDIR = 'user'
_COOKIE_PRIVATE_KEY = 'sirepo_cookie_private_key'


def install_user_d(compt, j2_ctx):
    run_d = systemd.unit_run_d(j2_ctx, 'sirepo')
    compt.install_access(mode='700', owner=j2_ctx.rsconf_db.run_u)
    compt.install_directory(run_d)
    db_d = run_d.join(_DB_SUBDIR)
    compt.install_directory(db_d)
    user_d = db_d.join(_USER_SUBDIR)
    compt.install_directory(user_d)
    return user_d


class T(component.T):
    def internal_build(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker_registry
        from rsconf.component import docker

        self.buildt.require_component('docker', 'nginx', 'db_bkp')
        j2_ctx = self.hdb.j2_ctx_copy()
        z = j2_ctx.sirepo
        run_d = systemd.docker_unit_prepare(self, j2_ctx)
        z.db_d = run_d.join(_DB_SUBDIR)
        z.run_u = j2_ctx.rsconf_db.run_u
        cookie_name = z.get('cookie_name', 'sirepo_{}'.format(j2_ctx.rsconf_db.channel))
        docker_hosts = z.get('docker_hosts')
        z.setdefault('feature_config', pkcollections.Dict())
        # TODO(robnagler) write a yml file that gets read by pkconfig
        params = pkcollections.Dict({
            'pykern.pkconfig.channel': j2_ctx.rsconf_db.channel,
            'pykern.pkdebug.redirect_logging': True,
            'pykern.pkdebug.want_pid_time': True,
            'sirepo.cookie.http_name': cookie_name,
            'sirepo.cookie.private_key':  self.secret_path_value(
                _COOKIE_PRIVATE_KEY,
                gen_secret=lambda: base64.urlsafe_b64encode(os.urandom(32)),
                visibility='channel',
            )[0],
            'sirepo.feature_config.api_modules': z.feature_config.get('api_modules', []),
            'sirepo.pkcli.service.ip': '0.0.0.0',
            'sirepo.pkcli.service.run_dir': run_d,
            'sirepo.runner.docker.image': docker_registry.absolute_image(j2_ctx, z.docker_image),
            'sirepo.runner.job_class': 'Docker' if docker_hosts else 'Celery',
            'sirepo.server.db_dir': z.db_d,
        })
        _params_copy(
            params,
            j2_ctx,
            (
                'sirepo.pkcli.service_port',
                'sirepo.pkcli.service_processes',
                'sirepo.pkcli.service_threads',
            ),
        )
        if docker_hosts:
            docker_tls_d = run_d.join('docker_tls')
            params['sirepo.runner.docker.hosts'] = docker_hosts
            params['sirepo.runner.docker.tls_dir'] = docker_tls_d
            _params_copy(params, j2_ctx, ('sirepo.mpi_cores',))
        else:
            _params_copy(params, j2_ctx, ('sirepo.celery_tasks.broker_url',))
        self._comsol(params, j2_ctx)
        self._auth(params, j2_ctx)
        install_user_d(self, j2_ctx)
        self.install_access(mode='400')
        nginx.install_vhost(
            self,
            vhost=z.vhost,
            backend_host=j2_ctx.rsconf_db.host,
            backend_port=z.pkcli.service_port,
            j2_ctx=j2_ctx,
        )
        db_bkp.install_script_and_subdir(
            self,
            j2_ctx,
            run_u=z.run_u,
            run_d=run_d,
        )
        if docker_hosts:
            docker.setup_cluster(
                self,
                docker_hosts,
                docker_tls_d,
                run_u=z.run_u,
                j2_ctx=j2_ctx,
            )
        env = {}
        for k in sorted(params.keys()):
            env[k.upper().replace('.', '_')] = _env_value(params[k])
        # Only variable that is required to be in the environment
        env['PYTHONUNBUFFERED'] = '1'
        systemd.docker_unit_enable(
            self,
            j2_ctx,
            image=docker_registry.absolute_image(j2_ctx, z.docker_image),
            env=env,
            cmd='sirepo service uwsgi',
            after=[] if docker_hosts else ['celery_sirepo.service'],
            #TODO(robnagler) wanted by nginx
        )


    def _auth(self, params, j2_ctx):
        a = j2_ctx.get('sirepo').get('auth')
        if not a:
            # deprecated mode
            if j2_ctx.nested_get('sirepo.oauth.github_secret'):
                _params_copy(
                    params,
                    j2_ctx,
                    (
                        'sirepo.oauth.github_key',
                        'sirepo.oauth.github_secret',
                    ),
                )
                params['sirepo.feature_config.api_modules'].append('oauth')
            return
        methods = a.methods + a.deprecated_methods
        decl = {
            'basic': [
                'password',
                'uid',
            ],
            'email': [
                'from_email',
                'from_name',
                'smtp_password',
                'smtp_server',
                'smtp_user',
            ],
            'github': [
#TODO(robnagler) remove after in prod 5/31/2019
                'callback_uri',
                'key',
                'secret',
            ],
        }
        for m, names in decl.items():
            if m not in methods:
                continue
            _params_copy(
                params,
                j2_ctx,
                ['sirepo.auth.{}.{}'.format(m, n) for n in names],
                validate=True,
            )
        _params_copy(
            params,
            j2_ctx,
            (
                'sirepo.auth.methods',
                'sirepo.auth.deprecated_methods',
            ),
        )

    def _comsol(self, params, j2_ctx):
        r = j2_ctx.sirepo.get('comsol_register')
        if not r:
            return
        e = r.get('mail_username')
        _params_copy(
            params,
            j2_ctx,
            (
                'sirepo.comsol_register.mail_password',
                'sirepo.comsol_register.mail_server',
                'sirepo.comsol_register.mail_username',
            ),
        )
        params['sirepo.comsol_register.mail_support_email'] = e
        params['sirepo.comsol_register.mail_recipient_email'] = e
        params['sirepo.feature_config.api_modules'].append('comsol_register')


def _env_value(v):
    if isinstance(v, (tuple, list)):
        return pkconfig.TUPLE_SEP.join(v)
    return str(v)


def _params_copy(params, j2_ctx, keys, validate=False):
    for k in keys:
        params[k] = j2_ctx.nested_get(k)
        if validate:
            assert params[k], \
                'key={} has no value'.format(k)
