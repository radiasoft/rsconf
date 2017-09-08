#!/bin/bash

base_users_main() {
    rsconf_require base_os
    rsconf_radia_run_as_user root home
    rsconf_install_access 400 root root
    rsconf_install root/.post_bivio_bashrc
    rsconf_radia_run_as_user vagrant home
    set +e +o pipefail
    . ~/.bashrc
    set -e -o pipefail
}
