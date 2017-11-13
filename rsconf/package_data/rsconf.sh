#!/bin/bash
#
# Development server:
# python -m SimpleHTTPServer 8000
#
# Development box:
# curl radia.run | bash -s vagrant-centos7
# vssh
# sudo su -
# export install_server=http://v5.bivio.biz:8000 install_channel=dev
# curl "$install_server" | bash -s rsconf.sh
#
rsconf_edit() {
    local file=$1
    local grep=$2
    local perl=$3
    if [[ ! -e $file ]]; then
        # file doesn't exist so ok
        return 1
    fi
    # No $perl ($3) means append exactly this line
    if [[ -z $perl ]]; then
        if fgrep -s -q -x "$grep" "$file"; then
            return 1
        fi
        echo "$grep" >> "$file"
    else
        local need=
        if [[ $grep =~ ^![[:space:]]*(.+) ]]; then
            need=1
            grep=${BASH_REMATCH[1]}
        fi
        local g=$( set +e; grep -s -q "$grep" "$file" && echo 1 )
        if [[ $g != $need ]]; then
            return 1
        fi
        perl -pi -e "$perl" "$file"
        g=$( set +e; grep -s -q "$grep" "$file" && echo 1 )
        if [[ $g == $need ]]; then
            install_err "$perl: failed to modify: $file"
        fi
    fi
    rsconf_service_file_check "$file"
    return 0
}

rsconf_install_access() {
    if [[ ! $1 =~ ^[[:digit:]]{1,4}$ ]]; then
        install_err "$1: invalid or empty mode"
    fi
    rsconf_install_access[mode]=$1
    if [[ -z $2 ]]; then
        return
    fi
    rsconf_install_access[user]=$2
    rsconf_install_access[group]=${3:-${rsconf_install_access[user]}}
}

rsconf_install_chxxx() {
    local path=$1
    local actual=( $(stat --format '%a %U %G' "$path") )
    local change=
    if [[ -z ${rsconf_install_access[group]} ]]; then
        install_err 'rsconf_install_access must be called first'
    fi
    if [[ ${rsconf_install_access[user]} != ${actual[1]} ]]; then
        chown "${rsconf_install_access[user]}" "$path"
        change=1
    fi
    if [[ ${rsconf_install_access[group]} != ${actual[2]} ]]; then
        chgrp "${rsconf_install_access[group]}" "$path"
        change=1
    fi
    if [[ ${rsconf_install_access[mode]} != ${actual[0]} ]]; then
        chmod "${rsconf_install_access[mode]}" "$path"
        change=1
    fi
    if [[ -z $rsconf_no_check && -n $change ]]; then
        rsconf_service_file_check "$path"
    fi
}

rsconf_install_directory() {
    local path=$1
    if [[ -L $path ]]; then
        install_err "$path: is a symbolic link, expecting a directory"
    fi
    if [[ -d $path ]]; then
        rsconf_install_chxxx "$path"
        return
    fi
    if [[ -e $path ]]; then
        install_err "$path: exists but is not a directory"
    fi
    # parent directory must already exist
    mkdir "$path"
    rsconf_no_check=1 rsconf_install_chxxx "$path"
    rsconf_service_file_check "$path"
}

rsconf_install_file() {
    local path=$1
    local tmp
    if [[ -d "$path" ]]; then
        install_err "$path: is a directory, must be a file (remove first)"
    fi
    tmp=$path-rsconf-tmp
    install_download "$path" > "$tmp"
    # Unlikely we are downloading HTML so this is a sanity check on SimpleHTTPServer
    # returning something that's a directory listing or not found
    if grep -s -q -i '^<title>' "$tmp"; then
        install_err "$path: unexpected HTML file (directory listing?)"
    fi
    if cmp "$tmp" "$path" >& /dev/null; then
        rm -f "$tmp"
        rsconf_install_chxxx "$path"
        return
    fi
    rsconf_no_check=1 rsconf_install_chxxx "$tmp"
    mv -f "$tmp" "$path"
    rsconf_service_file_check "$path"
}

rsconf_main() {
    local host=${1:-$(hostname -f)}
    if [[ $host =~ / ]]; then
        install_err "$host: invalid host name"
    fi
    install_curl_flags+=( -n )
    install_url host/$host
    # Dynamically scoped; must be inline here
    local -A rsconf_install_access=()
    local -A rsconf_service_status=()
    local -A rsconf_service_watch=()
    local -a rsconf_service_order=()
    install_script_eval 000.sh
    rsconf_service_restart
}

rsconf_radia_run_as_user() {
    local user=$1
    shift
    (cat <<EOF; curl -L -S -s http://radia.run) | su - "$user" -c "bash -s $*"
install_server=''
install_channel=$install_channel
install_debug=$install_debug
install_verbose=$install_verbose
EOF
}

rsconf_reboot() {
    install_err "Reboot required"
}

rsconf_require() {
    rsconf_only_once=1 rsconf_run "$1"
}

rsconf_run() {
    local script=$1
    shift
    local f=${script}_rsconf_component
    if ! type "$f" >& /dev/null; then
        install_script_eval "$script.sh"
    elif [[ -n $rsconf_only_once ]]; then
        return
    fi
    rsconf_install_access=()
    "$f" "$@"
}

rsconf_service_docker_pull() {
    local service=$1
    local image=$2
    local container_image_id=$(docker inspect --format='{{.Image}}' "$service" 2>/dev/null || true)
    local prev_id=$(docker inspect --format='{{.Id}}' "$image" 2>/dev/null || true)
    install_info "docker pull $image (may take awhile)..."
    install_exec docker pull "$image"
    local curr_id=$(docker inspect --format='{{.Id}}' "$image" 2>/dev/null || true)
    if [[ $prev_id != $curr_id || -n $container_image_id && $container_image_id != $curr_id ]]; then
        install_info "$image: new image, restart $service required"
        rsconf_service_status[$service]=restart
    fi
}


rsconf_service_file_check() {
    local path=$1
    local s
    while [[ $path != / ]]; do
        s=${rsconf_service_watch[$path]}
        if [[ -n $s ]]; then
            rsconf_service_status[$s]=restart
            return
        fi
        path=$(dirname "$path")
    done
}

rsconf_service_prepare() {
    local s=$1
    local w
    rsconf_service_status[$s]=start
    rsconf_service_order+=( $s )
    for w in "$@"; do
        if [[ -n ${rsconf_service_watch[$w]} ]]; then
            install_err "$w: already being watched by ${rsconf_service_watch[$w]}, also wanted by $s"
        fi
        rsconf_service_watch[$w]=$s
    done
}

rsconf_service_restart() {
    local reloaded= s
    for s in ${rsconf_service_order[@]}; do
        if [[ ${rsconf_service_status[$s]} == restart ]]; then
            if [[ $reloaded ]]; then
               reloaded=1
               systemctl daemon-reload
            fi
            # Just restart, most daemons are fast
            systemctl restart "$s"
            install_info "$s: restarting"
        else
            # test is really only necessary for the msg
            if ! systemctl is-active "$s" >&/dev/null; then
                install_info "$s: starting"
                systemctl start "$s"
            fi
        fi
        systemctl enable "$s"
    done
}

rsconf_yum_install() {
    local x todo=()
    for x in "$@"; do
        if ! rpm -q "$x" >& /dev/null; then
            todo+=( "$x" )
        fi
    done
    if (( ${#todo[@]} > 0 )); then
        yum install --color=never -y -q "${todo[@]}"
    fi
}

rsconf_main "${install_extra_args[@]}"