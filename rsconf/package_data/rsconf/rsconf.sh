#!/bin/bash
set -euo pipefail

rsconf_append() {
    declare file=$1
    declare egrep=$2
    # Default $egrep is $line and $egrep is fgrep for exact match
    declare line=${3:-}
    if [[ ! $line ]]; then
        line=$egrep
        egrep=
    fi
    if [[ ! -e $file ]]; then
        install_err "$file: does not exist"
    fi
    # Assumes file must exist or be writable
    if [[ $egrep ]]; then
        if grep -E -s -q -- "$egrep" "$file"; then
            return ${rsconf_edit_no_change_res:-1}
        fi
    elif grep -F -s -q -x -- "$line" "$file"; then
        return ${rsconf_edit_no_change_res:-1}
    fi
    echo "$line" >> "$file"
    rsconf_service_file_changed "$file"
    return 0
}

rsconf_append_authorized_key() {
    declare user=$1
    declare key=$2
    declare ssh_d="$( getent passwd "$user" | cut -d: -f6 )"/.ssh
    if [[ ! -e "$ssh_d" ]]; then
        install -d -m 700 -o "$user" -g "$user" "$ssh_d"
    fi
    declare keys_f=$ssh_d/authorized_keys
    if [[ ! -e $keys_f ]]; then
        install -m 600 -o "$user" -g "$user" /dev/null "$keys_f"
    fi
    rsconf_edit_no_change_res=0 rsconf_append "$keys_f" "$key"
}

rsconf_clone_repo() {
    declare repo=$1
    declare dest=$2
    declare owner=$3
    if [[ ! -d $dest || ! $(ls -A "$dest") ]]; then
        (umask 027 && git clone "$repo" "$dest")
    fi
    chown -R "$owner": "$dest"
}

rsconf_edit() {
    # Update $file with $edit_perl if $need_egrep is not found
    #
    # $need_egrep is an egrep regex. If found, then $rsconf_edit_no_change_res
    # is returned (default: 1). If $need_egrep, begins with a
    # bang ("!") then the opposite test happens: if $need_egrep is found,
    # then the edit *does* happen.
    #
    # $edit_perl is a perl expression passed to `perl -pi -e`. If $edit_perl
    # does not modify the file in a way that satisfies $need_egrep, then
    # an error is raised.
    #
    # rsconf_service_file_changed is called in the event of changes.
    declare file=$1
    declare need_egrep=$2
    declare edit_perl=$3
    if [[ ! -e $file ]]; then
        install_err "$file: does not exist"
    fi
    declare need=
    if [[ $need_egrep =~ ^![[:space:]]*(.+) ]]; then
        need=1
        egrep=${BASH_REMATCH[1]}
    fi
    declare g=$( egrep -s -q -- "$need_egrep" "$file" && echo 1 || true )
    if [[ $g != $need ]]; then
        return ${rsconf_edit_no_change_res:-1}
    fi
    perl -pi -e "$edit_perl" "$file"
    g=$( grep -E -s -q -- "$need_egrep" "$file" && echo 1 || true )
    if [[ $g == $need ]]; then
        install_err "$edit_perl: failed to modify: $file"
    fi
    rsconf_service_file_changed "$file"
    return 0
}

rsconf_fedora_release_if() {
    # First supported release is 27, but this allows a general fedora test
    declare expect=${1:-26}
    [[ $install_os_release_id == fedora ]] && (( $expect >= $install_os_release_version_id ))
}

rsconf_file_hash() {
    declare file=$1
    declare x=( $(md5sum "$file" 2>/dev/null) )
    echo ${x[0]:-NONE}
}

rsconf_file_hash_check() {
    declare file=$1
    if [[ ! ${rsconf_file_hash[$file]:-} ]]; then
        install_err "$file: missing hash"
    fi
    declare new=$(rsconf_file_hash "$file")
    declare old=${rsconf_file_hash[$file]}
    unset rsconf_file_hash[$file]
    if [[ $new != $old ]]; then
        rsconf_service_file_changed "$file"
    fi
}

rsconf_file_hash_save() {
    declare file=$1
    if [[ ${rsconf_file_hash[$file]:-} ]]; then
        install_err "$file: unchecked saved hash"
    fi
    rsconf_file_hash[$file]=$(rsconf_file_hash "$file")
}

rsconf_unchecked_gid() {
    declare group=$1
    cut -d: -f3 <(getent group "$group") || true
}

rsconf_group() {
    declare group=$1
    declare gid=$2
    declare exist_gid=$(rsconf_unchecked_gid "$group")
    if [[ $exist_gid ]]; then
        if [[ $exist_gid != $gid ]]; then
            install_err "$exist_gid: unexpected gid (expect=$gid) for group $group"
        fi
        return
    fi
    declare flags=()
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
    declare path=$1
    declare actual=( $(stat --format '%a %U %G' "$path") )
    declare change=
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
    declare path=$1
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
    declare parent=$(dirname "$path")
    if [[ ! -e $parent ]]; then
        install_err "$path: parent directory ($parent) does not exist"
    fi
    rsconf_mkdir "$path"
    rsconf_no_check=1 rsconf_install_chxxx "$path"
    rsconf_service_file_changed "$path"
}

rsconf_install_ensure_file_exists() {
    declare path=$1
    if [[ -e $path ]]; then
        if [[ -L $path && ! -f $path ]]; then
            install_err "$path: is a link or not a plain file"
        fi
        rsconf_install_chxxx "$path"
        return
    fi
    # parent directory must already exist
    declare parent=$(dirname "$path")
    if [[ ! -e $parent ]]; then
        install_err "$path: parent directory ($parent) does not exist"
    fi
    touch "$path"
    rsconf_no_check=1 rsconf_install_chxxx "$path"
    rsconf_service_file_changed "$path"
}

rsconf_install_file() {
    declare path=$1
    declare md5=${2:-}
    declare tmp
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
    declare path=$1
    if [[ -e $path ]]; then
        if [[ -L $path || ! -d $path ]]; then
            install_err "$path: mount point is not a directory"
        fi
        return
    fi
    declare parent=$(dirname "$path")
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
    declare rpm_base=$1
    declare rpm_file=$2
    declare rpm_version=$3
    declare prev_version=$(rpm -q "$rpm_base" 2>&1 || true)
    # Yum is wonky with update/install. We have to handle
    # both fresh install and update, which install does, but
    # it doesn't return an error if the update isn't done.
    # You just have to check so this way is more robust
    declare install_cmd=
    if [[ $rpm_version == $prev_version ]]; then
        if rpm --verify "$rpm_base"; then
            return
        fi
        install_info "$rpm_version: rpm is modified, reinstalling"
        install_cmd=reinstall
    elif rsconf_is_perl_rpm_rollback "$prev_version" "$rpm_version"; then
        install_info "$rpm_version older than $prev_version, downgrading"
        install_cmd=downgrade
    fi
    declare tmp=$rpm_file
    install_download "$rpm_file" > "$tmp"
    if [[ ! $(file "$tmp" 2>/dev/null) =~ RPM ]]; then
        # Error messages from rpm -qp are strange:
        # "error: open of <html> failed: No such file or directory"
        install_err "$rpm_file: not found or not a valid RPM"
    fi
    rsconf_yum_install_cmd=$install_cmd rsconf_yum_install "$tmp"
    rm -f "$tmp"
    declare curr_rpm=$(rpm -q "$rpm_base")
    if [[ $curr_rpm != $rpm_version ]]; then
        install_err "$curr_rpm: did not get installed, new=$rpm_version"
    fi
    rsconf_service_file_changed "$rpm_file"
}

rsconf_install_rpm_key() {
    # installs a custom rpm_key if not already installed
    declare rpm_key=$1
    if rpm -q "$rpm_key" &> /dev/null; then
        return
    fi
    declare tmp=$rpm_key-rsconf-tmp
    install_download "$rpm_key" > "$tmp"
    if [[ ! $(file "$tmp" 2>/dev/null) =~ public.key ]]; then
        install_err "rpm_key=$rpm_key not found or not a valid rpm key file=$tmp"
    fi
    rpm --import "$tmp"
    rm -f "$tmp"
}

rsconf_install_symlink() {
    declare old=$1
    declare new=$2
    if [[ -L $new ]]; then
        declare e=$(readlink "$new")
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

rsconf_is_perl_rpm_rollback() {
    declare prev_version=$1
    declare install_version=$2
    if ! rsconf_perl_rpm_version prev_version "$prev_version"; then
        return 1
    fi
    if ! rsconf_perl_rpm_version install_version "$install_version"; then
        install_err "program error install_version=$install_version"
    fi
    if [[ ! ${install_version:-} ]]; then
        install_err "internal error with rsconf_perl_rpm_version parsing (install_version=$2)"
    fi
    [[ $prev_version > $install_version ]]
}

rsconf_main() {
    # POSIT: radiasoft/download/bin/install.sh: skip repo arg
    if [[ ${1+$1} == rsconf.sh ]]; then
        shift
    fi
    declare host=${1:-$(hostname -f)}
    declare setup_dev=${2:-}
    if [[ $host =~ / ]]; then
        install_err "$host: invalid host name"
    fi
    if [[ $setup_dev == setup_dev ]]; then
        rsconf_setup_dev "$host"
    fi
    install_curl_flags+=( --netrc )
    install_info "$host: rsconf begin"
    install_url host/$host
    # Dynamically scoped; must be inline here
    declare -A rsconf_file_hash=()
    declare -A rsconf_install_access=()
    declare -A rsconf_service_file_changed=()
    declare -A rsconf_service_restart_at_end=()
    declare -A rsconf_service_status=()
    declare -A rsconf_service_watch=()
    declare -a rsconf_service_order=()
    declare rsconf_rerun_required=
    install_script_eval 000.sh
    rsconf_at_end=1 rsconf_service_restart
    if [[ $rsconf_rerun_required ]]; then
        install_info "$rsconf_rerun_required

You need to rerun this command"
    fi
}

rsconf_mkdir() {
    declare d=$1
    # Create the directory (and parents) with strict permissions;
    # Subsequent permissions will be created after
    install -d -o root -g root -m 700 "$d"
}

rsconf_perl_rpm_version() {
    declare var=$1
    declare rpm=$2
    if [[ ! $rpm =~ -([[:digit:]]{8}\.[[:digit:]]{6}) ]]; then
        if [[ $rpm =~ not.installed ]]; then
            return 1
        fi
        install_err "invalid version format rpm=$rpm"
    fi
    eval "$var='${BASH_REMATCH[1]}'"
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
    declare script=$1
    shift
    declare f=${script}_rsconf_component
    if ! type "$f" >& /dev/null; then
        install_script_eval "$script.sh"
    elif [[ $rsconf_only_once ]]; then
        return
    fi
    rsconf_install_access=()
    "$f" "$@"
}

rsconf_service_docker_pull() {
    declare image=$1
    declare service=${2:-}
    declare container_name=${3:-$service}
    declare static_files_gen=${4:-true}
    if [[ $service ]]; then
        declare container_image_id=$(docker inspect --format='{{.Image}}' "$container_name" 2>/dev/null || true)
        declare prev_id=$(docker inspect --format='{{.Id}}' "$image" 2>/dev/null || true)
    fi
    install_info "docker pull $image (may take awhile)..."
    install_exec docker pull "$image"
    declare f=
    if [[ $service ]]; then
        declare curr_id=$(docker inspect --format='{{.Id}}' "$image" 2>/dev/null || true)
        if [[ $prev_id != $curr_id || $container_image_id && $container_image_id != $curr_id ]]; then
            install_info "$image: new image, restart $service required"
            rsconf_service_trigger_restart "$service"
            f=1
        fi
    fi
    static_files_gen_force=$f "$static_files_gen"
}

rsconf_service_file_changed() {
    declare path=$1
    rsconf_service_file_changed[$path]=1
}

rsconf_service_file_changed_check() {
    declare service=$1
    declare w c
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
    declare service=$1
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
    declare s
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
            rsconf_systemctl restart "$s"
            rsconf_service_status[$s]=active
        elif [[ ${rsconf_service_status[$s]} == active ]]; then
            # Only one re/start per install
            continue
        fi
        if [[ ${rsconf_service_status[$s]} == start ]]; then
            # https://askubuntu.com/a/836155
            # don't use "status", b/c reports "bad" for sysv init
            # scripts (e.g. network)
            if ! rsconf_systemctl is-active "$s"; then
                install_info "$s: starting"
                rsconf_systemctl start "$s"
            fi
            rsconf_service_status[$s]=active
        fi
        rsconf_systemctl enable "$s"
    done
    # And reload at end, because rsconf_systemctl_clean_unit may have run
    systemctl daemon-reload
}

rsconf_service_restart_at_end() {
    declare s=$1
    rsconf_service_restart_at_end[$s]=1
}

rsconf_service_trigger_restart() {
    declare service=$1
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
    declare host=$1
    export install_channel=dev
    install_download "$install_server/$host-netrc" > /root/.netrc
    chmod 400 /root/.netrc
}

rsconf_setup_vars() {
    declare channel=$1
    declare id=$2
    declare version=$3
    export install_channel=$channel
    if [[ $install_os_release_id != $id ]]; then
        install_err "invalid os_release_id=$install_os_release_id expecting=$id"
    fi
    if  [[ $install_os_release_version_id != $version ]]; then
        install_err "invalid os_release_version_id=$install_os_release_version_id expecting=$version"
    fi
}

rsconf_systemctl() {
    declare op=$1
    declare service=$2
    declare s=$service
    # Handles multi-instance services (sirepo@{1..3}) and regular services
    if [[ $service =~ (.*)@ ]]; then
        s=${BASH_REMATCH[1]}
    fi
    # systemctl makes managing instances pretty awkward.
    # No commands understand brace expansion although that's the
    # recommended syntax (implying shell expansion).
    # "$s@*" expansion doesn't work for enable/disable.
    # This handles switching from single instance to several instances (and back).
    case $op in
        enable)
            # disable works, because it matches enabled services
            systemctl disable "$s" /etc/systemd/system/multi-user.target.wants/"$s"@* &> /dev/null || true
            # do not quote for sirepo@{1..3} case
            eval systemctl enable $service
            rsconf_systemctl_clean_unit "$s" "$service"
            ;;
        is-active)
            # is-active doesn't do the right thing so test individually
            declare x
            # do not quote for sirepo@{1..3} case
            for x in $(eval echo $service); do
                if ! systemctl is-active $x &> /dev/null; then
                    return 1
                fi
            done
            return 0
            ;;
        restart)
            # Handle special case restarts, like NetworkManager
            declare n=rsconf_systemctl_restart_${s//-/_}
            if type -f "$n" &> /dev/null; then
                install_info "Executing: $n"
                "$n"
                return
            else
                # stop works, because it matches running services
                systemctl stop "$s" "$s@*" &> /dev/null || true
            fi
            # fall through to start
            ;&
        start)
            # do not quote for sirepo@{1..3} case
            eval systemctl start $service
            ;;
        *)
            install_err "unknown systemctl op=$op for service=$service"
            ;;
    esac
}

rsconf_systemctl_clean_unit() {
    declare basename=$1
    declare maybe_template_name=$2
    declare x=
    if [[ $basename == $maybe_template_name ]]; then
        # Remove the template
        x=@
    fi
    # POSIT: rsconf_service_restart runs systemctl daemon-reload
    rm -f "/etc/systemd/system/$basename$x.service"
}

rsconf_user() {
    declare user=$1
    declare uid=$2
    declare exist_uid=$(id -u "$user" 2>/dev/null || true)
    rsconf_group "$user" "$gid"
    if [[ $exist_uid ]]; then
        if [[ $exist_uid != $uid ]]; then
            install_err "$exist_uid: unexpected uid (expect=$uid) for user $user"
        fi
        return
    fi
    declare flags=()
    #POSIT: <1000 is system
    if [[ $gid < 1000 ]]; then
        flags+=( -r )
    fi
    useradd "${flags[@]}" -g "$user" -u "$uid" "$user"
}

rsconf_yum_install() {
    declare x todo=()
    for x in "$@"; do
        if ! rpm -q "$x" >& /dev/null; then
            todo+=( "$x" )
        fi
    done
    if (( ${#todo[@]} > 0 )); then
        _rsconf_yum_install "${todo[@]}"
    fi
}

rsconf_yum_install_url() {
    declare base=$1
    declare url=$2
    if rpm -q "$base" >& /dev/null; then
        return
    fi
    _rsconf_yum_install "$url"
}

_rsconf_yum_install() {
    declare todo=( "$@" )
    declare cmd="${rsconf_yum_install_cmd:-install}"
    if [[ ! $cmd =~ ^((re)?install|downgrade)$ ]]; then
        install_err "unexpected value rsconf_yum_install_cmd=$cmd"
    fi
    if ! yum "$cmd" --color=never -y -q "${todo[@]}"; then
        install_err "FAILED: yum $cmd ${todo[*]}";
    fi
}
