base_users_main() {
    rsconf_require base-os
    (
        set -e -o pipefail
        rsconf_run_installer home
        cat > /root/.post_bivio_bashrc <<EOF
export SYSTEMD_COLORS=0
# --quit-if-one-screen -quit-at-eof --quit-on-intr --no-init
export SYSTEMD_LESS=EFKX
EOF
        chmod 600 /root/.post_bivio_bashrc
    )
    if (( $? != 0 )); then
        install_err 'root environment install failed'
    fi
    rsconf_run_installer_as_user vagrant radiasoft/home-env
}
