#!/bin/bash
# usage: source $0

initdb_do() {
    sudo su - 'vagrant' <<'EOF'
    set -euo pipefail
    export BCONF='/srv/petshop/bivio.bconf'
    bivio sql init_dbms || true
    bivio sql -f create_test_db
        echo initdb_post_cmd

EOF
    if type rsconf_service_trigger_restart >& /dev/null; then
        rsconf_service_trigger_restart 'petshop'
    fi
}

initdb_main() {
    if [[ ! -d /srv/petshop/db/RealmFile ]]; then
        # Have to stop the service so postgres doesn't hang
        systemctl stop 'petshop' >& /dev/null || true
        initdb_do
    elif [[ ${initdb_weekly:-} ]]; then
        echo "${BASH_SOURCE[0]}: recreating test db" 1>&2
        # Have to stop the service so postgres doesn't hang
        systemctl stop 'petshop'
        initdb_do
        systemctl start 'petshop'
    fi
}

initdb_main
