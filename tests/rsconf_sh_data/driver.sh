#!/bin/bash
source "$1"

install_err() { echo "install_err: $*" >&2; exit 1; }
install_info() { echo "install_info: $*" >&2; }
yum() { printf 'yum'; printf ' [%s]' "$@"; printf '\n'; }

rpm() {
    if [[ $1 != --query ]]; then
        echo "unexpected: rpm $*" >&2
        exit 1
    fi
    if [[ $2 == --package ]]; then
        if ! grep --no-messages --quiet --extended-regexp \
            '^[a-z]+-[0-9]+\.[0-9]+-[0-9]+\.x86_64$' "${!#}"; then
            return 1
        fi
        cat "${!#}"
        return
    fi
    [[ $2 == installed || $2 == installed-1.0-1.x86_64 ]]
}

cmd() {
    declare rsconf_yum_install_cmd=$1
    shift
    "$@"
}

t() {
    declare label=$1
    shift
    declare rc=0 out=
    out=$( "$@" 2>&1 ) || rc=$?
    out=${out//$PWD\//}
    if [[ $out ]]; then
        out=" $out"
    fi
    printf '%-34s rc=%s%s\n' "$label" "$rc" "$out"
}

arg=
set_arg() {
    case $1 in
        name-installed) arg=installed;;
        name-missing) arg=missing;;
        nevra-installed) arg=installed-1.0-1.x86_64;;
        group) arg='@Development Tools';;
        empty) arg=;;
        file-older) echo installed-0.9-1.x86_64 > perl-dev.rpm; arg=perl-dev.rpm;;
        file-same) echo installed-1.0-1.x86_64 > perl-dev.rpm; arg=perl-dev.rpm;;
        file-newer) echo installed-2.0-1.x86_64 > perl-dev.rpm; arg=perl-dev.rpm;;
        file-other) echo missing-2.0-1.x86_64 > perl-dev.rpm; arg=perl-dev.rpm;;
        file-invalid) echo '<html>not a package</html>' > perl-dev.rpm; arg=perl-dev.rpm;;
        file-abspath) echo installed-0.9-1.x86_64 > perl-dev.rpm; arg=$PWD/perl-dev.rpm;;
        *) echo "unexpected: set_arg $1" >&2; exit 1;;
    esac
}

declare -a cmds=( unset install reinstall downgrade bogus )
declare -a args=(
    name-installed
    name-missing
    nevra-installed
    group
    empty
    file-older
    file-same
    file-newer
    file-other
    file-invalid
    file-abspath
)

declare c a v
for f in _rsconf_need_yum_install rsconf_yum_install; do
    echo "== $f =="
    for c in "${cmds[@]}"; do
        v=$c
        if [[ $c == unset ]]; then
            v=
        fi
        for a in "${args[@]}"; do
            set_arg "$a"
            t "$c $a" cmd "$v" "$f" "$arg"
        done
    done
    echo
done

echo '== rsconf_yum_install_url =='
for c in "${cmds[@]}"; do
    v=$c
    if [[ $c == unset ]]; then
        v=
    fi
    for a in name-installed name-missing nevra-installed empty; do
        set_arg "$a"
        t "$c $a" cmd "$v" rsconf_yum_install_url "$arg" http://x/u.rpm
    done
done
