#!/bin/bash
#
# To run: curl radia.run | bash -s rsconf host
#
rsconf_install() {
    local f
    for path in "$@"; do
        local path=$1
        if [[ $path =~ ^/ ]]; then
            install_err "$path: path must not be absolute"
        fi
        local abs=/$path
        if [[ $path =~ /$ ]]; then
            if [[ -L $abs ]]; then
                install_err "$abs: is a symbolic link, expecting a directory"
            fi
            if [[ ! -d $abs ]]; then
                if [[ -e $abs ]]; then
                    install_err "$abs: exists but is not a directory"
                fi
                # parent directory must exist
                mkdir "$abs"
            fi
            rsconf_install_chxxx "$abs"
            return
        fi
        if [[ -d "$abs" ]]; then
            install_err "$abs: is a directory, must be a file (remove first)"
        fi
        local tmp=$abs-tmp
        install_download "$file" > "$tmp"
        if cmp "$tmp" "$abs" >& /dev/null; then
            rm -f "$tmp"
            rsconf_install_chxxx "$abs"
            return
        fi
        rsconf_install_chxxx "$tmp"
        mv -f "$tmp" "$abs"
    done
}

declare -A rsconf_install_access=( [mode]=400 [user]=root [group]=root )

rsconf_install_access() {
    if [[ $1 =~ ^[[:digit:]]{1,4}$ ]]; then
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
    if [[ ${rsconf_install_access[user]} != ${actual[1]} ]]; then
        chown "$owner" "$path"
    fi
    if [[ ${rsconf_install_access[group]} != ${actual[2]} ]]; then
        chgrp "$group" "$path"
    fi
    if [[ ${rsconf_install_access[mode]} != ${actual[0]} ]]; then
        chmod "$mode" "$path"
    fi
}

rsconf_main() {
    local host=${1:-$(hostname -f)}
    if [[ $host =~ / ]]; then
        install_err "$host: invalid host name"
    fi
    install_url radiasoft/rsconf "srv/$host"
    install_script_eval 00.sh
    rsconf_run "${a[@]}"
}

rsconf_radia_run_as_user() {
    local user=$1
    shift
    (cat <<EOF; curl "$install_server") | su - "$user" -c bash -s "$@"
install_channel=$install_channel
install_debug=$install_debug
install_server=$install_server
install_verbose=$install_verbose
EOF
}

declare -A rsconf_require

rsconf_require() {
    local x
    for x in "$@"; do
        if [[ -z ${rsconf_require[$x]} ]]; then
            rsconf_require[$x]=start
            rsconf_run "$x"
            rsconf_require[$x]=done
        fi
    done
}

rsconf_run() {
    local op=$1
    shift
    local f=${op}_main
    if ! type "$f" >& /dev/null; then
        install_script_eval "$op.sh"
    fi
    "$f" "$@"
}

rsconf_main "${install_extra_args[@]}"
