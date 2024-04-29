#!/bin/bash
cd '/srv/sirepo/db/user'

#TODO(robnagler) copied from sirepo/misc/expunge.sh
# changed default days to 30 and removed "$@" passed to expunge_main
set -e -u -o pipefail
DEFAULT_DAYS=30

expunge_one() {
    local mmin=$1
    local u=$2
    for f in $(find "$u"/*/*/* -prune -type d -mmin +"$mmin"); do
        if [[ $f =~ /[a-zA-Z0-9]{8}/[^/]+$ ]]; then
            echo "removing report: $f" 1>&2
            rm -rf "$f"
        fi
    done
}

expunge_main() {
    local days=${1:-$DEFAULT_DAYS}
    # sanity check number
    local mmin=$(( $days * 24 * 60 ))
    local u
    if [[ ! $PWD =~ /user$ ]]; then
        echo 'Must be run from user directory' 1>&2
        exit 1
    fi
#TODO(robnagler) how to decide whom to expunge
    return
    local reg=' never-match '
    if [[ -f '/srv/sirepo/db/auth.db' ]]; then
        reg=" $(echo $(echo 'select uid from user_registration_t;' | sqlite3 -batch '/srv/sirepo/db/auth.db') ) "
    fi
    for u in *; do
        if [[ $u =~ ^[a-zA-Z0-9]{8}$ && ! $reg =~ " $u " ]]; then
            expunge_one "$mmin" "$u"
        fi
    done
}

expunge_main
