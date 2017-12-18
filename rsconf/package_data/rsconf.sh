#!/bin/bash
#
# rsconf library and main
#
rsconf_append() {
    local file=$1
    local line=$2
    if [[ ! -e $file ]]; then
        install_err "$file: does not exist"
    fi
    # Assumes file must exist or be writable
    if fgrep -s -q -x "$line" "$file"; then
        return ${rsconf_edit_no_change_res:-1}
    fi
    echo "$line" >> "$file"
    rsconf_service_file_changed "$file"
    return 0
}

rsconf_edit() {
    local file=$1
    local grep=$2
    local perl=$3
    if [[ ! -e $file ]]; then
        install_err "$file: does not exist"
    fi
    local need=
    if [[ $grep =~ ^![[:space:]]*(.+) ]]; then
        need=1
        grep=${BASH_REMATCH[1]}
    fi
    local g=$( set +e; grep -s -q "$grep" "$file" && echo 1 )
    if [[ $g != $need ]]; then
        return ${rsconf_edit_no_change_res:-1}
    fi
    perl -pi -e "$perl" "$file"
    g=$( set +e; grep -s -q "$grep" "$file" && echo 1 )
    if [[ $g == $need ]]; then
        install_err "$perl: failed to modify: $file"
    fi
    rsconf_service_file_changed "$file"
    return 0
}

rsconf_fedora_release_if() {
    # First supported release is 27, but this allows a general fedora test
    local expect=${1:-26}
    local ver=( $(cat /etc/fedora-release 2>/dev/null) )
    [[ ${ver[2]} =~ ^[0-9]+$ ]] && (( $expect >= ${ver[2]} ))
}

rsconf_file_hash() {
    local file=$1
    local x=( $(md5sum "$file" 2>/dev/null) )
    echo ${x[0]:-NONE}
}

rsconf_file_hash_check() {
    local file=$1
    if [[ ! $rsconf_file_hash[$file] ]]; then
        install_err "$file: missing hash"
    fi
    local new=$(rsconf_file_hash "$file")
    local old=${rsconf_file_hash[$file]}
    unset rsconf_file_hash[$file]
    if [[ $new != $old ]]; then
        rsconf_service_file_changed "$file"
    fi
}

rsconf_file_hash_save() {
    local file=$1
    if [[ ${rsconf_file_hash[$file]} ]]; then
        install_err "$file: unchecked saved hash"
    fi
    rsconf_file_hash[$file]=$(rsconf_file_hash "$file")
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
        rsconf_service_file_changed "$path"
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
    rsconf_service_file_changed "$path"
}

rsconf_install_file() {
    local path=$1
    local src=$2
    local tmp
    if [[ -d "$path" ]]; then
        install_err "$path: is a directory, must be a file (remove first)"
    fi
    tmp=$path-rsconf-tmp
    if [[ $src ]]; then
        # Don't copy attributes, because may be /dev/null
        cp "$src" "$tmp"
    else
        install_download "$path" > "$tmp"
    fi
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
    rsconf_service_file_changed "$path"
}

rsconf_main() {
    local host=${1:-$(hostname -f)}
    local setup_dev=$2
    if [[ $host =~ / ]]; then
        install_err "$host: invalid host name"
    fi
    if [[ $setup_dev == setup_dev ]]; then
        rsconf_setup_dev "$host"
    fi
    install_curl_flags+=( -n )
    install_url host/$host
    # Dynamically scoped; must be inline here
    local -A rsconf_file_hash=()
    local -A rsconf_install_access=()
    local -A rsconf_service_status=()
    local -A rsconf_service_watch=()
    local -a rsconf_service_order=()
    local rsconf_rerun_required=
    install_script_eval 000.sh
    rsconf_service_restart
    if [[ $rsconf_rerun_required ]]; then
        echo "$rsconf_rerun_required

You need to rerun this command"
    fi
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

rsconf_rerun_required() {
    rsconf_rerun_required="$rsconf_rerun_required$1
"
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
        rsconf_service_trigger_restart "$service"
    fi
}

rsconf_service_file_changed() {
    local path=$1
    local s
    while [[ $path != / ]]; do
        s=${rsconf_service_watch[$path]}
        if [[ -n $s ]]; then
            rsconf_service_trigger_restart "$s"
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
            install_info "$s: restarting"
            systemctl restart "$s"
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

rsconf_service_trigger_restart() {
    local service=$1
    rsconf_service_status[$service]=restart
}

rsconf_setup_dev() {
    local host=$1
    export install_channel=dev
    curl "$install_server/$host-netrc" > /root/.netrc
    chmod 400 /root/.netrc
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
