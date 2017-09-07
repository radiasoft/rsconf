#!/bin/bash
sirepo_main() {
    rsconf_require docker
    rsconf_install_access 400 root
    rsconf_install etc/systemd/system/sirepo.service
    rsconf_install_access 700 "$rsconf_run_user"
    rsconf_install var/lib/sirepo/{,db/}
    rsconf_install_access 500
    rsconf_install var/lib/sirepo/{cmd,env,remove,start,stop}
    systemctl daemon-reload
    systemctl start sirepo
    systemctl enable sirepo
}
