#!/bin/bash
rs_mariadb_rsconf_component() {
rsconf_service_prepare 'rs_mariadb' '/etc/systemd/system/rs_mariadb.service' '/etc/systemd/system/rs_mariadb.service.d' '/srv/rs_mariadb'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/rs_mariadb'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/rs_mariadb/cmd' '3ca0657054a51e20b9c68fa6908c7197'
rsconf_install_file '/srv/rs_mariadb/env' '22e03a134cc868bb12094d8dc118a6c4'
rsconf_install_file '/srv/rs_mariadb/remove' '323e4d381bae6272daf1c5d93f88235c'
rsconf_install_file '/srv/rs_mariadb/start' '4657124da5c8697b8bb84e38b257d300'
rsconf_install_file '/srv/rs_mariadb/stop' '8d6b79f845b3d8c3e62ab9f501f5eb12'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/rs_mariadb.service' '23dbf6765628072b175e539cbb9a43b9'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/rs_mariadb/db'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/rs_mariadb/my.cnf' 'd4152da8262b4bd38805e87b4aff2806'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/rs_mariadb/db_bkp.sh' 'f542704cd36beffa3659a673d6f74313'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/rs_mariadb/db_bkp'
rs_mariadb_main
rsconf_service_restart
}
#!/bin/bash

rs_mariadb_init() {
    #NOTE: $db should be a non-conflicting name so we can avoid using
    #   mysql backticks for quoting (create database `$db`), which results
    # in: "wp1: command not found" because of the EOF (here) doc.
    local db=$1
    local user=$2
    local pw=$3
    docker exec -i rs_mariadb bash <<EOF
set -euo pipefail
export MYSQL_PWD='mqpass'
if mysql -h '127.0.0.1' -P '7011' -u root -e 'use $db';
 then
    exit
fi
mysql -h '127.0.0.1' -P '7011' -u root <<'EOF2'
CREATE DATABASE $db;
GRANT ALL PRIVILEGES ON $db.* TO '$user'@'%' IDENTIFIED BY '$pw';
FLUSH PRIVILEGES;
EOF2
EOF
}

rs_mariadb_main() {
    # if this directory exists, then db was initialized
    if [[ -e  /srv/rs_mariadb/db/mysql ]]; then
        return
    fi

    /srv/rs_mariadb/start /bin/bash <<'EOF'
    set -euo pipefail
    # cross-bootstrap avoids referring to a host name, which inside a docker
    # container is irrelevant. mysql_install_db is a complex beast so we'll
    # run it, but it's probaby only one line of code that needs to be run. The
    # rest are checks that are irrelevant to us. It has to run as root.
    mysql_install_db --cross-bootstrap --datadir='/srv/rs_mariadb/db'
EOF
    # Now intitialize the database, removing the "test" db and any users
    # which were created by mysql_install_db.
    /srv/rs_mariadb/start /bin/bash <<'EOF'
    set -euo pipefail
    init_log='/srv/rs_mariadb/db_init.log'
    mysqld --init-file=/dev/stdin <<'EOF2' >& "$init_log" &
        DELETE FROM mysql.user;
        CREATE USER 'root'@'%' IDENTIFIED BY 'mqpass';
        GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;
        DROP DATABASE IF EXISTS test;
        FLUSH PRIVILEGES;
EOF2
    # fastest path to stopping server after it processes init-file and starts
    # serving. You can't exit from the init-file, and you can't use
    # https://mariadb.com/kb/en/library/mysql_secure_installation/
    # b/c it requires sudo
    pid=$!
    for x in $(seq 10); do
        sleep 1
        if grep 'ready for connections' "$init_log" >& /dev/null; then
            break
        fi
    done
    # Normal termination
    kill -TERM "$pid"
    for x in $(seq 10); do
        sleep 1
        if ! kill -0 "$pid" >& /dev/null; then
            exit 0
        fi
    done
    kill -KILL "$pid"
    exit 1
EOF
}

