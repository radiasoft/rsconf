# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from pykern import pkcompat
from pykern import pkconfig
from pykern.pkdebug import pkdp
from rsconf import component
from rsconf import db
from rsconf import systemd
import base64
import os


_DB_SUBDIR = 'db'

_USER_SUBDIR = 'user'

_PROPRIETARY_CODE_SUBDIR = 'proprietary_code'

#: secret basename
_COOKIE_PRIVATE_KEY = 'sirepo_cookie_private_key'

#: secret basename
_SERVER_SECRET = 'sirepo_job_server_secret'


class T(component.T):
    def internal_build_compile(self):
        from rsconf.component import docker_registry
        from rsconf import db

        self.__docker_unit_enable_after = []
        self.__uwsgi_docker_vols = []

        self.buildt.require_component('docker', 'nginx', 'db_bkp')
        jc, z = self.j2_ctx_init()
        self.__run_d = systemd.docker_unit_prepare(self, jc)
        d = self.__run_d.join(_DB_SUBDIR)
        self.j2_ctx_pksetdefault(PKDict(
            sirepo=PKDict(
                cookie=PKDict(
                    http_name=lambda: 'sirepo_{}'.format(jc.rsconf_db.channel),
                    private_key=lambda: self.secret_path_value(
                        _COOKIE_PRIVATE_KEY,
                        gen_secret=lambda: pkcompat.from_bytes(
                            base64.urlsafe_b64encode(os.urandom(32)),
                        ),
                        visibility='channel',
                    )[0],
                ),
                docker_image=docker_registry.absolute_image(self),
                feature_config=PKDict(
                    api_modules=[],
                    job=True,
                    # TODO(e-carlin): Remove and use only moderated_sim_types once
                    # git.radiasoft.org/sirepo/pull/4211 is in prod.
                    default_proprietary_sim_types=tuple(),
                    moderated_sim_types=tuple(),
                    proprietary_sim_types=tuple(),
                    proprietary_code_tarballs=tuple(),
                ),
                job=PKDict(
                    max_message_bytes='200m',
                ),
                pkcli=PKDict(
                    service=PKDict(
                        ip='0.0.0.0',
                        run_dir=self.__run_d,
                    ),
                ),
                srdb=PKDict(root=d),
                wordpress_host=None,
            ),
            pykern=PKDict(
                pkdebug=PKDict(
                    redirect_logging=True,
                    want_pid_time=True,
                ),
                pkconfig=PKDict(channel=jc.rsconf_db.channel),
            ),
        ))
        self._comsol(z)
        self._jupyterhublogin(z)
        self.j2_ctx_pksetdefault(PKDict(
            sirepo=PKDict(
                client_max_body_size=pkconfig.parse_bytes(z.job.max_message_bytes),
                job_api=PKDict,
                job_driver=PKDict(modules=['docker']),
                job=PKDict(
                    server_secret=lambda: self.secret_path_value(
                        _SERVER_SECRET,
                        gen_secret=lambda: pkcompat.from_bytes(
                            base64.urlsafe_b64encode(os.urandom(32)),
                        ),
                        visibility='channel',
                    )[0],
                    verify_tls=lambda: jc.pykern.pkconfig.channel != 'dev',
                ),
                pkcli=PKDict(
                    job_supervisor=PKDict(
                        ip='127.0.0.1',
                        port=8001,
                    ),
                ),
            ),
        ))
        # server connects locally only so go direct to tornado.
        # supervisor has different uri to pass to agents.
        z.job_api.supervisor_uri = 'http://{}:{}'.format(
            z.pkcli.job_supervisor.ip,
            z.pkcli.job_supervisor.port,
        )
        self._set_sirepo_config('sirepo_job_supervisor')
#TODO(robnagler) remove when deployed to alpha
        z.job.supervisor_uri = z.job_api.supervisor_uri

    def internal_build_write(self):
        from rsconf.component import db_bkp
        from rsconf.component import nginx
        from rsconf.component import docker

        jc = self.j2_ctx
        z = jc[self.name]
        self._install_dirs_and_files()
        nginx.install_vhost(
            self,
            vhost=z.vhost,
            backend_host=jc.rsconf_db.host,
            backend_port=z.pkcli.service_port,
            j2_ctx=jc,
        )
        systemd.docker_unit_enable(
            self,
            jc,
            image=z.docker_image,
            env=self.sirepo_unit_env(),
            cmd='sirepo service uwsgi',
            after=self.__docker_unit_enable_after,
            #TODO(robnagler) wanted by nginx
            volumes=self.__uwsgi_docker_vols,
        )
        db_bkp.install_script_and_subdir(
            self,
            jc,
            run_u=jc.rsconf_db.run_u,
            run_d=self.__run_d,
        )

    def sirepo_unit_env(self, compt=None):
        if not compt:
            compt = self
        # Only variable that is required to be in the environment
        e = pkconfig.to_environ(
            ['*'],
            values=PKDict((k, v) for k, v in compt.j2_ctx.items() if k in ('sirepo', 'pykern')),
            # local only values
            exclude_re=r'^sirepo(?:_docker_image|.*_vhost|.*_client_max_body)',
        )
        e.PYTHONUNBUFFERED = '1'
        return e

    def _comsol(self, z):
        r = z.get('comsol_register')
        if not r:
            return
        e = r.get('mail_username')
        r.pksetdefault(
            mail_support_email=e,
            mail_recipient_email=e,
        )
        z.pknested_get('feature_config.api_modules').append('comsol_register')

    def _install_dirs_and_files(self):
        jc = self.j2_ctx
        z = jc[self.name]
        self.install_access(mode='700', owner=jc.rsconf_db.run_u)
        self.install_directory(self.__run_d)
        d = self.__run_d.join(_DB_SUBDIR)
        self.install_directory(d)
        self.install_directory(d.join(_USER_SUBDIR))
        if not z.feature_config.proprietary_code_tarballs:
            return
        p = d.join(_PROPRIETARY_CODE_SUBDIR)
        self.install_directory(p)
        for c in z.feature_config.proprietary_code_tarballs:
            self.install_directory(p.join(c))
        self.install_access(mode='400')
        for c in z.feature_config.proprietary_code_tarballs:
            self.install_abspath(
                self.proprietary_file(jc, c),
                p.join(c, c + '.tar.gz'),
            )

    def _jupyterhublogin(self, z):
        p = set(self.j2_ctx.sirepo.feature_config.get('default_proprietary_sim_types', []))
        m = set(self.j2_ctx.sirepo.feature_config.get('moderated_sim_types', []))
        z.using_moderated_sim_types = True
        if 'jupyterhublogin' in p:
            assert not m, \
                f'can only set one of default_proprietary_sim_types={p} or moderated_sim_types={m}'
            z.using_moderated_sim_types = False
        z.jupyterhub_enabled =  'jupyterhublogin' in p.union(m)
        if not z.jupyterhub_enabled:
            return
        self.__uwsgi_docker_vols.append(z.sim_api.jupyterhublogin.user_db_root_d)
        self._set_sirepo_config('sirepo_jupyterhub')

    def _set_sirepo_config(self, component):
        self.buildt.require_component(component)
        c = self.buildt.get_component(component)
        c.sirepo_config(self)
        self.__docker_unit_enable_after.append(c.name)
