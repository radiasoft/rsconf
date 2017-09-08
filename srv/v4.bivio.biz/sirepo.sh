#!/bin/bash
sirepo_main() {
    rsconf_require docker nginx
    # See Poettering's omniscience about what's good for all of us here:
    # https://github.com/systemd/systemd/issues/770
    # I would want these files to be 400, since there's no value in making them
    # public. The machines are inaccessiable to anybody who doesn't have root access.
    rsconf_install_access 444 root
    rsconf_install etc/systemd/system/sirepo.service
    rsconf_install_access 700 vagrant
    rsconf_install var/lib/sirepo/{,db/}
    rsconf_install_access 400
    rsconf_install var/lib/sirepo/db/beaker_secret
    rsconf_install_access 500
    rsconf_install var/lib/sirepo/{cmd,env,remove,start,stop}
#TODO(robnagler) when to download new version of docker container?
#TODO(robnagler) docker pull happens explicitly
#TODO(robnagler) only reload if a change, restart if a change
    systemctl daemon-reload
    systemctl start sirepo
    systemctl enable sirepo

# Sep 11 00:17:12 v4.bivio.biz start[18702]: CommandError: uwsgi only works if sirepo.server.cfg.job_queue=_Celery
}
