# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
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
_SERVER_SECRET = 'sirepo_job_server_secret'


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
    def internal_build_compile(self):
        from rsconf.component import docker_registry

        self.buildt.require_component('docker', 'nginx', 'db_bkp')
        jc, z = self.j2_ctx_copy()
        self.__run_d = systemd.docker_unit_prepare(self, jc)
        self.__run_u = jc.rsconf_db.run_u
        j = bool(z.get('job_driver'))
        self.j2_ctx_pksetdefault(dict(
            sirepo={
                'cookie': dict(
                    http_name=lambda: 'sirepo_{}'.format(jc.rsconf_db.channel),
                    private_key=lambda: self.secret_path_value(
                        _COOKIE_PRIVATE_KEY,
                        gen_secret=lambda: base64.urlsafe_b64encode(os.urandom(32)),
                        visibility='channel',
                    )[0],
                ),
                'docker_image': docker_registry.absolute_image(jc, z.docker_image),
                'feature_config': dict(
                    api_modules=[],
                    job=j,
                ),
                'pkcli.service': dict(
                    ip='0.0.0.0',
                    run_dir=self.__run_d,
                ),
                'server.db_dir': lambda: self.__run_d.join(_DB_SUBDIR),
            },
            pykern={
                pkdebug=dict(
                    redirect_logging=True,
                    want_pid_time=True,
                ),
                'pkconfig.channel': jc.rsconf_db.channel,
            },
        ))
        self._comsol(z)
        if j:
            self.j2_ctx_pksetdefault({
                'sirepo.pkcli.job_supervisor': dict(
                    ip='127.0.0.1',
                    port=8001,
                ),
                'sirepo.job.server_secret': lambda: self.secret_path_value(
                    _SERVER_SECRET,
                    gen_secret=lambda: base64.urlsafe_b64encode(os.urandom(32)),
                    visibility='channel',
                )[0],
            })
            s = self.get_component('sirepo_job_supervisor')
            s.sirepo_config(self)
            self.__docker_unit_enable_after = [s.name]
            # server connects locally only so no https
            self.j2_ctx_pksetdefault({
                'sirepo.job.supervisor_uri': lambda: 'http://{}:{}'.format(
                    z.pkcli.job_supervisor.ip,
                    z.pkcli.job_supervisor.port,
                ),
            })
        else:
            # REMOVE after Celery no longer in use
            self.j2_ctx_pksetdefault({
                'sirepo.runner.job_class': 'Celery',
            })

    def internal_build_write(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker

        install_user_d(self, jc)
        self.install_access(mode='400')
        nginx.install_vhost(
            self,
            vhost=z.vhost,
            backend_host=jc.rsconf_db.host,
            backend_port=z.pkcli.service_port,
            j2_ctx=jc,
        )
        db_bkp.install_script_and_subdir(
            self,
            jc,
            run_u=self.__run_u,
            run_d=self.__run_d,
        )
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            env=self.sirepo_unit_env(),
            cmd='sirepo service uwsgi',
            after=self.__docker_unit_enable_after,
            #TODO(robnagler) wanted by nginx
        )

    def sirepo_unit_env(compt=None):
        if not compt:
            compt = self
        # Only variable that is required to be in the environment
        e = pkconfig.to_environ(['sirepo.*', 'pykern.*'], compt.j2_ctx)
        e.PYTHONUNBUFFERED = '1'
        return e

    def _comsol(self, jc):
        r = z.get('comsol_register')
        if not r:
            return
        e = r.get('mail_username')
        r.pksetdefault(
            mail_support_email=e,
            mail_recipient_email=e,
        )
        z.pknested_get('feature_config.api_modules').append('comsol_register')
