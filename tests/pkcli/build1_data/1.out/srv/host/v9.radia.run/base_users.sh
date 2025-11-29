#!/bin/bash
base_users_rsconf_component() {
rsconf_append_authorized_key 'marysmith' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOrg8mRPQ8KPjJdZ6ebMYNFZgie7FglkhxNcoGzd2mdF marysmith@radia.run'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/root/.post_bivio_bashrc' '25bda14f81aa858d6a7f5a78444a5c14'
rsconf_append_authorized_key 'root' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIB3mhGsrxFV4KnHjDtBaaU7ZdlNhwxIEPZ3/+Bv1xZY v3.radia.run'
base_users_main
install_source_bashrc
}
#!/bin/bash

base_users_add() {
    declare name=$1
    declare uid=$2
    declare gid=$3
    declare want_shell=$4
    declare curr_gid=$(rsconf_unchecked_gid "$name")
    if [[ $curr_gid ]]; then
        if [[ $curr_gid != $gid ]]; then
            install_err "$curr_gid: expecting group $name=$gid"
        fi
    else
        groupadd -g "$gid" "$name"
    fi
    declare curr_uid=$(id -u "$name" 2>/dev/null || true)
    if [[ $curr_uid ]]; then
        if [[ $curr_uid != $uid ]]; then
            install_err "$curr_uid: expecting user $name=$uid"
        fi
        curr_gid=$(id -g "$name")
        if [[ $curr_gid != $gid ]]; then
            install_err "$curr_gid: expecing gid=$gid for user $name"
        fi
    else
        declare shell=
        if [[ ! $want_shell ]]; then
            shell=--shell=/sbin/nologin
        fi
        useradd -m -g "$gid" -u "$uid" "$name" $shell
    fi
    if [[ $want_shell ]]; then
        # Keep up to date in case needed by later code
        RADIA_RUN_BRANCH_HOME_ENV='' rsconf_radia_run_as_user "$name" home
    fi
}

base_users_main() {
    rsconf_radia_run_as_user root home
base_users_add 'joeblow' '2002' '2002' ''
base_users_add 'marysmith' '2003' '2003' ''
base_users_add 'vagrant' '1000' '1000' '1'

}

