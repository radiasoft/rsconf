#!/bin/bash
base_users_rsconf_component() {
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/root/.post_bivio_bashrc' '1bdc2408012083bb98396f73fe4d116e'
rsconf_append_authorized_key 'root' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIB3mhGsrxFV4KnHjDtBaaU7ZdlNhwxIEPZ3/+Bv1xZY v3.radia.run'
base_users_main
}
#!/bin/bash

base_users_add() {
    local name=$1
    local uid=$2
    local gid=$3
    local want_shell=$4
    local curr_gid=$(rsconf_unchecked_gid "$name")
    if [[ $curr_gid ]]; then
        if [[ $curr_gid != $gid ]]; then
            install_err "$curr_gid: expecting group $name=$gid"
        fi
    else
        groupadd -g "$gid" "$name"
    fi
    local curr_uid=$(id -u "$name" 2>/dev/null || true)
    if [[ $curr_uid ]]; then
        if [[ $curr_uid != $uid ]]; then
            install_err "$curr_uid: expecting user $name=$uid"
        fi
        curr_gid=$(id -g "$name")
        if [[ $curr_gid != $gid ]]; then
            install_err "$curr_gid: expecing gid=$gid for user $name"
        fi
    else
        local shell=
        if [[ ! $want_shell ]]; then
            shell=--shell=/sbin/nologin
        fi
        useradd -m -g "$gid" -u "$uid" "$name" $shell
    fi
    if [[ $want_shell ]]; then
        # Keep up to date in case needed by later code
        rsconf_radia_run_as_user "$name" home
    fi
}

base_users_main() {
    rsconf_radia_run_as_user root home
base_users_add 'joeblow' '2002' '2002' ''
base_users_add 'marysmith' '2003' '2003' ''
base_users_add 'vagrant' '1000' '1000' '1'

    set +euo pipefail
    . ~/.bashrc
    set -euo pipefail
}

