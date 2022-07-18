#!/bin/bash
set -eou pipefail
docker exec -i 'rs_mariadb' bash -s "$PWD" <<'EOF'
set -eou pipefail
cd "$1"
export MYSQL_PWD='mqpass'
for d in $(mysql --batch --disable-column-names -u root -e 'show databases'); do
    if [[ ! $d =~ ^(mysql|(information|performance)_schema)$ ]]; then
        # xz is not in the docker image so just use gzip
        # the databases are small. This is better than zipping
        # outside the container.
        mysqldump -u root "$d" | gzip -9 > "$d".sql.gz
    fi
done
EOF
