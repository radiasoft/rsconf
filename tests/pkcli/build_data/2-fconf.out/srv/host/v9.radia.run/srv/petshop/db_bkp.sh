#!/bin/bash
export BCONF='/srv/petshop/bivio.bconf'
export BIVIO_IO_ALERT_WANT_TIME=0
export BIVIO_IO_ALERT_WANT_PID=0
bivio sql export_db .
declare -a dirs=()
for d in '/srv/petshop/bkp' '/srv/petshop/logbop' \
    '/srv/petshop/db'/{RealmMail,RealmMailBounce,MailReceiveDispatchForm,LegacyClubUploadForm,OFXImportForm,DynamicsUpdate}; do
    # prevent failing on:
    # find: '/srv/petshop/db/MailReceiveDispatchForm': No such file or directory
    if [[ -d $d ]]; then
        dirs+=( "$d" )
    fi
done
find "${dirs[@]}" \
    \( -type f -mtime +'2' -exec rm -f {} \; \) \
    -o -type d -mtime +2 -empty -exec rmdir {} \; -prune;
find '/srv/petshop/db'/RealmFile -name '.*#*' -mtime +3 -exec rm -f {} \;
