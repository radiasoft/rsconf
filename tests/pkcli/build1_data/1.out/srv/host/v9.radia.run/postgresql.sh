#!/bin/bash
postgresql_rsconf_component() {
rsconf_install_access '700' 'postgres' 'postgres'
rsconf_yum_install postgresql-server
rsconf_install_directory '/var/log/postgresql'
postgresql_main
rsconf_service_prepare 'postgresql' '/etc/systemd/system/postgresql.service' '/etc/systemd/system/postgresql.service.d' '/srv/postgresql'
rsconf_append "/srv/postgresql/data/postgresql.conf" "include 'rsconf.conf'" || true
rsconf_install_access '400' 'postgres' 'postgres'
rsconf_install_file '/srv/postgresql/data/v9.radia.run.key' 'fe22a3a98b83d3cd8d48eb5ccda07d60'
rsconf_install_file '/srv/postgresql/data/v9.radia.run.crt' 'a6d3bba40727a12f03b1f44727bb98be'
rsconf_install_file '/srv/postgresql/data/rsconf.conf' '29917cbabfb8be75728963bc5fc9fcf2'
rsconf_install_file '/srv/postgresql/data/pg_hba.conf' 'f4fd85b06b4b4872ea041feabc69e351'
rsconf_install_access '400' 'root' 'root'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/logrotate.d/postgresql' 'cf86c6bc140606e3cba328f4a4fb2ea4'
rsconf_service_restart
}
#!/bin/bash

postgresql_install() {
    if [[ -e  /srv/postgresql/data/postgresql.conf ]]; then
        return
    fi
    local old=/var/lib/pgsql
    if [[ -L  $old ]]; then
        install_err "$old: is a symlink, need to yum reinstall postgresql-server"
    fi
    mv -f "$old" '/srv/postgresql'
    # postgresql-setup hardwires /var/lib/pgsql for logs so don't bother
    # with anything but a symlink. $PGDATA will remain /var/lib/pgsql/data,
    # and everything works fine
    ln --relative -s '/srv/postgresql' "$old"
    local pw=/tmp/postgresql_aux-$$-$RANDOM
    install -o postgres -m 400 /dev/null "$pw"
    echo 'pgpass' >> "$pw"
    local ret=0
    if ! PGSETUP_INITDB_OPTIONS="--pwfile=$pw --encoding=SQL_ASCII --auth=ident" postgresql-setup initdb; then
        ret=1
    fi
    rm -f "$pw"
    return "$ret"
}

postgresql_log() {
    local old=/var/lib/pgsql/data/pg_log
    if [[ ! -L $old ]]; then
        install -d -m 700 '/var/log/postgresql'
        # save the old logs, just in case
        for f in $(ls -tr "$old"/*.log 2>/dev/null || true); do
            cat $f >> '/var/log/postgresql/postgresql.log'
        done
        chown -R postgres:postgres '/var/log/postgresql'
        rm -rf "$old"
        ln -r -s '/var/log/postgresql' "$old"
    fi
}

postgresql_main() {
    postgresql_install
    postgresql_log
}

