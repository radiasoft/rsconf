#!/bin/bash
set -euo pipefail

rsconf_append() {
    local file=$1
    local egrep=$2
    # Default $egrep is $line and $egrep is fgrep for exact match
    local line=${3:-}
    if [[ ! $line ]]; then
        line=$egrep
        egrep=
    fi
    if [[ ! -e $file ]]; then
        install_err "$file: does not exist"
    fi
    # Assumes file must exist or be writable
    if [[ $egrep ]]; then
        if egrep -s -q -- "$egrep" "$file"; then
            return ${rsconf_edit_no_change_res:-1}
        fi
    elif fgrep -s -q -x -- "$line" "$file"; then
        return ${rsconf_edit_no_change_res:-1}
    fi
    echo "$line" >> "$file"
    rsconf_service_file_changed "$file"
    return 0
}

rsconf_append_authorized_key() {
    local user=$1
    local key=$2
    local ssh_d="$( getent passwd "$user" | cut -d: -f6 )"/.ssh
    if [[ ! -e "$ssh_d" ]]; then
        install -d -m 700 -o "$user" -g "$user" "$ssh_d"
    fi
    local keys_f=$ssh_d/authorized_keys
    if [[ ! -e $keys_f ]]; then
        install -m 600 -o "$user" -g "$user" /dev/null "$keys_f"
    fi
    rsconf_edit_no_change_res=0 rsconf_append "$keys_f" "$key"
}

rsconf_edit() {
    local file=$1
    local egrep=$2
    local perl=$3
    if [[ ! -e $file ]]; then
        install_err "$file: does not exist"
    fi
    local need=
    if [[ $egrep =~ ^![[:space:]]*(.+) ]]; then
        need=1
        egrep=${BASH_REMATCH[1]}
    fi
    local g=$( egrep -s -q -- "$egrep" "$file" && echo 1 || true )
    if [[ $g != $need ]]; then
        return ${rsconf_edit_no_change_res:-1}
    fi
    perl -pi -e "$perl" "$file"
    g=$( egrep -s -q -- "$egrep" "$file" && echo 1 || true )
    if [[ $g == $need ]]; then
        install_err "$perl: failed to modify: $file"
    fi
    rsconf_service_file_changed "$file"
    return 0
}

rsconf_fedora_release_if() {
    # First supported release is 27, but this allows a general fedora test
    local expect=${1:-26}
    [[ $install_os_release_id == fedora ]] && (( $expect >= $install_os_release_version_id ))
}

rsconf_file_hash() {
    local file=$1
    local x=( $(md5sum "$file" 2>/dev/null) )
    echo ${x[0]:-NONE}
}

rsconf_file_hash_check() {
    local file=$1
    if [[ ! ${rsconf_file_hash[$file]:-} ]]; then
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
    if [[ ${rsconf_file_hash[$file]:-} ]]; then
        install_err "$file: unchecked saved hash"
    fi
    rsconf_file_hash[$file]=$(rsconf_file_hash "$file")
}

rsconf_unchecked_gid() {
    local group=$1
    cut -d: -f3 <(getent group "$group") || true
}

rsconf_group() {
    local group=$1
    local gid=$2
    local exist_gid=$(rsconf_unchecked_gid "$group")
    if [[ $exist_gid ]]; then
        if [[ $exist_gid != $gid ]]; then
            install_err "$exist_gid: unexpected gid (expect=$gid) for group $group"
        fi
        return
    fi
    local flags=()
    #POSIT: <1000 is system
    if [[ $gid < 1000 ]]; then
        flags+=( -r )
    fi
    groupadd "${flags[@]}" -g "$gid" "$group"
}

rsconf_install_access() {
    if [[ ! $1 =~ ^[[:digit:]]{1,4}$ ]]; then
        install_err "$1: invalid or empty mode"
    fi
    rsconf_install_access[mode]=$1
    if [[ ! ${2:-} ]]; then
        return
    fi
    rsconf_install_access[user]=$2
    rsconf_install_access[group]=${3:-${rsconf_install_access[user]}}
}

rsconf_install_chxxx() {
    local path=$1
    local actual=( $(stat --format '%a %U %G' "$path") )
    local change=
    if [[ ! ${rsconf_install_access[group]} ]]; then
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
    if [[ ! ${rsconf_no_check:-} && $change ]]; then
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
    local parent=$(dirname "$path")
    if [[ ! -e $parent ]]; then
        install_err "$path: parent directory ($parent) does not exist"
    fi
    rsconf_mkdir "$path"
    rsconf_no_check=1 rsconf_install_chxxx "$path"
    rsconf_service_file_changed "$path"
}

rsconf_install_ensure_file_exists() {
    local path=$1
    if [[ -e $path ]]; then
        if [[ -L $path && ! -f $path ]]; then
            install_err "$path: is a link or not a plain file"
        fi
        rsconf_install_chxxx "$path"
        return
    fi
    # parent directory must already exist
    local parent=$(dirname "$path")
    if [[ ! -e $parent ]]; then
        install_err "$path: parent directory ($parent) does not exist"
    fi
    touch "$path"
    rsconf_no_check=1 rsconf_install_chxxx "$path"
    rsconf_service_file_changed "$path"
}

rsconf_install_file() {
    local path=$1
    local md5=${2:-}
    local tmp
    if [[ -d "$path" ]]; then
        install_err "$path: is a directory, must be a file (remove first)"
    fi
    if [[ $md5 ]] && echo "$md5 $path" | md5sum -c --strict >& /dev/null; then
        rsconf_install_chxxx "$path"
        return
    fi
    tmp=$path-rsconf-tmp
    install_download "$path" > "$tmp"
    # Unlikely we are downloading HTML so this is a sanity check on SimpleHTTPServer
    # returning something that's a directory listing or not found
    if grep -s -q -i '^<title>' "$tmp"; then
        install_err "$path: unexpected HTML file (directory listing?)"
    fi
    if [[ ! $md5 ]] && cmp "$tmp" "$path" >& /dev/null; then
        rm -f "$tmp"
        rsconf_install_chxxx "$path"
        return
    fi
    rsconf_no_check=1 rsconf_install_chxxx "$tmp"
    mv -f "$tmp" "$path"
    rsconf_service_file_changed "$path"
}

rsconf_install_mount_point() {
    local path=$1
    if [[ -e $path ]]; then
        if [[ -L $path || ! -d $path ]]; then
            install_err "$path: mount point is not a directory"
        fi
        return
    fi
    local parent=$(dirname "$path")
    if [[ ! -e $parent ]]; then
        # Create the parent directory with strict permission (root & 700),
        # because component may need to set permissions, and this maybe a
        # prerequisite (e.g. logical_volume) for the component.
        rsconf_mkdir "$parent"
    fi
    rsconf_install_directory "$path"
}

rsconf_install_perl_rpm() {
    # installs a custom rpm from the local repo
    local rpm_base=$1
    local rpm_file=$2
    local rpm_version=$3
    local prev_version=$(rpm -q "$rpm_base" 2>&1 || true)
    # Yum is wonky with update/install. We have to handle
    # both fresh install and update, which install does, but
    # it doesn't return an error if the update isn't done.
    # You just have to check so this way is more robust
    local reinstall=
    if [[ $rpm_version == $prev_version ]]; then
        if rpm --verify "$rpm_base"; then
            return
        fi
        install_info "$rpm_version: rpm is modified, reinstalling"
        reinstall=1
    fi
    local tmp=$rpm_file
    install_download "$rpm_file" > "$tmp"
    if [[ ! $(file "$tmp" 2>/dev/null) =~ RPM ]]; then
        # Error messages from rpm -qp are strange:
        # "error: open of <html> failed: No such file or directory"
        install_err "$rpm_file: not found or not a valid RPM"
    fi
    rsconf_yum_reinstall=$reinstall rsconf_yum_install "$tmp"
    rm -f "$tmp"
    local curr_rpm=$(rpm -q "$rpm_base")
    if [[ $curr_rpm != $rpm_version ]]; then
        install_err "$curr_rpm: did not get installed, new=$rpm_version"
    fi
    rsconf_service_file_changed "$rpm_file"
}

rsconf_install_symlink() {
    local old=$1
    local new=$2
    if [[ -L $new ]]; then
        local e=$(readlink "$new")
        if [[ $e == $old ]]; then
            return
        fi
        rm -f "$new"
    else
        if [[ -e $new ]]; then
            install_err "$new: path is exists and is not a symlink"
        fi
    fi
    ln -s "$old" "$new"
    if [[ ! -e "$new" ]]; then
        install_err "$new: symlinks to $old but does not exist"
    fi
    rsconf_service_file_changed "$new"
}

rsconf_main() {
    # POSIT: radiasoft/download/bin/install.sh: skip repo arg
    if [[ ${1+$1} == rsconf.sh ]]; then
        shift
    fi
    local host=${1:-$(hostname -f)}
    local setup_dev=${2:-}
    if [[ $host =~ / ]]; then
        install_err "$host: invalid host name"
    fi
    if [[ $setup_dev == setup_dev ]]; then
        rsconf_setup_dev "$host"
    fi
    install_curl_flags+=( -n )
    install_info "$host: rsconf begin"
    install_url host/$host
    # Dynamically scoped; must be inline here
    local -A rsconf_file_hash=()
    local -A rsconf_install_access=()
    local -A rsconf_service_file_changed=()
    local -A rsconf_service_restart_at_end=()
    local -A rsconf_service_status=()
    local -A rsconf_service_watch=()
    local -a rsconf_service_order=()
    local rsconf_rerun_required=
    install_script_eval 000.sh
    rsconf_at_end=1 rsconf_service_restart
    if [[ $rsconf_rerun_required ]]; then
        echo "$rsconf_rerun_required

You need to rerun this command"
    fi
}

rsconf_mkdir() {
    local d=$1
    # Create the directory (and parents) with strict permissions;
    # Subsequent permissions will be created after
    install -d -o root -g root -m 700 "$d"
}

rsconf_radia_run_as_user() {
    install_repo_as_user "$@"
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
    elif [[ $rsconf_only_once ]]; then
        return
    fi
    rsconf_install_access=()
    "$f" "$@"
}

rsconf_service_docker_pull() {
    local image=$1
    local service=${2:-}
    if [[ $service ]]; then
        local container_image_id=$(docker inspect --format='{{.Image}}' "$service" 2>/dev/null || true)
        local prev_id=$(docker inspect --format='{{.Id}}' "$image" 2>/dev/null || true)
    fi
    install_info "docker pull $image (may take awhile)..."
    install_exec docker pull "$image"
    if [[ $service ]]; then
        local curr_id=$(docker inspect --format='{{.Id}}' "$image" 2>/dev/null || true)
        if [[ $prev_id != $curr_id || $container_image_id && $container_image_id != $curr_id ]]; then
            install_info "$image: new image, restart $service required"
            rsconf_service_trigger_restart "$service"
        fi
    fi
}

rsconf_service_file_changed() {
    local path=$1
    rsconf_service_file_changed[$path]=1
}

rsconf_service_file_changed_check() {
    local service=$1
    local w c
    for w in ${rsconf_service_watch[$service]}; do
        for c in "${!rsconf_service_file_changed[@]}"; do
            if [[ $c == $w || $c =~ ^$w/ ]]; then
                rsconf_service_trigger_restart "$service"
                return
            fi
        done
    done
}

rsconf_service_prepare() {
    local service=$1
    rsconf_service_status[$service]=start
    if [[ $service == reboot ]]; then
       if [[ ! ${rsconf_service_watch[$service]:-} ]]; then
           rsconf_service_order+=( $service )
           rsconf_service_restart_at_end $service
       fi
       rsconf_service_watch[$service]+="$* "
       return
    fi
    rsconf_service_order+=( $service )
    if [[ ${rsconf_service_watch[$service]:-} ]]; then
        install_err "$service: rsconf_service_prepare is not re-entrant"
    fi
    # POSIT: No spaces or specials
    rsconf_service_watch[$service]="$*"
}

rsconf_service_restart() {
    if [[ ${rsconf_service_no_restart:-} ]]; then
        return
    fi
    local s
    # Always reload at start. Just easier and more reliable
    systemctl daemon-reload
    for s in ${rsconf_service_order[@]}; do
        if [[ ! ${rsconf_at_end:-} && ${rsconf_service_restart_at_end[$s]:+1} ]]; then
            continue
        fi
        if [[ ${rsconf_service_status[$s]} == start ]]; then
            rsconf_service_file_changed_check "$s"
        fi
        if [[ $s == reboot ]]; then
            # reboot.service not a real service
            continue
        fi
        if [[ ${rsconf_service_status[$s]} == restart ]]; then
            # Just restart, most daemons are fast
            install_info "$s: restarting"
            systemctl restart "$s"
            rsconf_service_status[$s]=active
        elif [[ ${rsconf_service_status[$s]} == active ]]; then
            # Only one re/start per install
            continue
        fi
        if [[ ${rsconf_service_status[$s]} == start ]]; then
            # https://askubuntu.com/a/836155
            # don't use "status", b/c reports "bad" for sysv init
            # scripts (e.g. network)
            if ! systemctl is-active "$s" >&/dev/null; then
                install_info "$s: starting"
                systemctl start "$s"
            fi
            rsconf_service_status[$s]=active
        fi
        systemctl enable "$s"
    done
}

rsconf_service_restart_at_end() {
    local s=$1
    rsconf_service_restart_at_end[$s]=1
}

rsconf_service_trigger_restart() {
    local service=$1
    if [[ $service == reboot ]]; then
        rsconf_reboot
        # does not return
    fi
    # Only trigger restart once
    if [[ ! ${rsconf_service_status[$service]:-} =~ active|restart ]]; then
        rsconf_service_status[$service]=restart
    fi
}

rsconf_setup_dev() {
    local host=$1
    export install_channel=dev
    curl "$install_server/$host-netrc" > /root/.netrc
    chmod 400 /root/.netrc
}

rsconf_user() {
    local user=$1
    local uid=$2
    local exist_uid=$(id -u "$user" 2>/dev/null || true)
    rsconf_group "$user" "$gid"
    if [[ $exist_uid ]]; then
        if [[ $exist_uid != $uid ]]; then
            install_err "$exist_uid: unexpected uid (expect=$uid) for user $user"
        fi
        return
    fi
    local flags=()
    #POSIT: <1000 is system
    if [[ $gid < 1000 ]]; then
        flags+=( -r )
    fi
    useradd "${flags[@]}" -g "$user" -u "$uid" "$user"
}

rsconf_yum_install() {
    local x todo=()
    for x in "$@"; do
        if ! rpm -q "$x" >& /dev/null; then
            todo+=( "$x" )
        fi
    done
    local cmd=install
    if [[ ${rsconf_yum_reinstall:-} ]]; then
        cmd=reinstall
    fi
    if (( ${#todo[@]} > 0 )); then
        yum "$cmd" --color=never -y -q "${todo[@]}"
    fi
}

rsconf_main ${install_extra_args[@]+"${install_extra_args[@]}"}
