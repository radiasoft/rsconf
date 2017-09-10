# -*- coding: utf-8 -*-
u"""create sirepo configuration

:copyright: Copyright (c) 2017 Bivio Software, Inc.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function

_DB_SUBDIR = 'db'

class T(component.T):
    def internal_build(self):
        from rsconf import systemd

        self.buildt.require_component('docker', 'rabbitmq', 'celery_sirepo', 'nginx')
        run_d = systemd.docker_unit_run_d(self)
        db_d = run_d.join(_DB_SUBDIR)
        hdb = self.hdb
        env=pkcollections.Dict(
            PYKERN_PKCONFIG_CHANNEL=hdb.channel,
            PYKERN_PKDEBUG_REDIRECT_LOGGING=1,
            PYKERN_PKDEBUG_WANT_PID_TIME=1,
            PYTHONUNBUFFERED=1,
            SIREPO_PKCLI_SERVICE_IP=0.0.0.0,
            SIREPO_PKCLI_SERVICE_RUN_DIR=run_d,
            SIREPO_SERVER_BEAKER_SESSION_KEY='sirepo_{}'.format(hdb.channel),
            SIREPO_SERVER_BEAKER_SESSION_SECRET=db_d.join('beaker_secret'),
            SIREPO_SERVER_DB_DIR=db_d,
            SIREPO_SERVER_JOB_QUEUE=Celery,
        )
        for f in (
            'pykern_pkdebug_control',
            'sirepo_celery_tasks_broker_url',
            'sirepo_mpi_cores',
            'sirepo_pkcli_service_port',
            'sirepo_pkcli_service_processes',
            'sirepo_pkcli_service_threads',
            'sirepo_oauth_github_key',
            'sirepo_oauth_github_secret',
            'sirepo_server_oauth_login',
        ):
            env[f.upper()] = hdb[f]
        systemd.docker_unit(
            self,
            image='radiasoft/sirepo',
            env=env,
            after=['docker.service', 'celery_sirepo.service'],
        )
        install db_dir
            'var/lib/sirepo/db/user',
        and user_dir
        # create the secret file

        self.create secret
            two alphas(?), not really, may have different os, no that is a tree
            alpha.yml
            alpha-sirepo.yml
            v4.bivio.biz.yml
            v4.bivio.biz-sshd-host-key - add to backup machine
            look for a secret by name alpha-sirepo-beaker_secret
            how to generate(?) - provided by caller
            if the secret is not defined, it is generated
            secrets can be stored in files (key, private, crt)
            get secret by (system, component, host)
               channel has a single secret for sirepo (always a component)
            each component on a host has a channel, secret is stored with that

        db_d
        compt.install_dir(
            mode='700',
            owner='vagrant',
        )

        self.install_file(
    #create if does not already exist in secret
            'var/lib/sirepo/db/beaker_secret',
            mode='400',
            owner='vagrant',
        )
    #If anything changes, restart service, otherwise just start
        rabbitmq depends on docker
        sirepo depends on celery_sirepo
        nginx server depends on sirepo
        those relationships are in "after"
        but also need to be elsewhere.
        systemctl daemon-reload
        systemctl start sirepo
        systemctl enable sirepo

#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly
#TODO(robnagler) only reload if a change, restart if a change
