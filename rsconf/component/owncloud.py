

set in /etc/entrypoint.d/50-folders.sh
OWNCLOUD_VOLUME_ROOT=/mnt/data
export OWNCLOUD_VERSION=10.0
export OWNCLOUD_DOMAIN=localhost
export OWNCLOUD_ADMIN_USERNAME=admin
export OWNCLOUD_ADMIN_PASSWORD=admin
export OWNCLOUD_HTTP_PORT=80
export OWNCLOUD_HTTPS_PORT=443

docker volume create owncloud_files

docker run -d \
  --name owncloud \
  --link mariadb:db \
  --link redis:redis \
  -p 80:80 \
  -p 443:443 \
  -e OWNCLOUD_DOMAIN=${OWNCLOUD_DOMAIN} \
  -e OWNCLOUD_DB_TYPE=mysql \
  -e OWNCLOUD_DB_NAME=owncloud \
  -e OWNCLOUD_DB_USERNAME=owncloud \
  -e OWNCLOUD_DB_PASSWORD=owncloud \
  -e OWNCLOUD_DB_HOST=db \
  -e OWNCLOUD_ADMIN_USERNAME=${OWNCLOUD_ADMIN_USERNAME} \
  -e OWNCLOUD_ADMIN_PASSWORD=${OWNCLOUD_ADMIN_PASSWORD} \
  -e OWNCLOUD_REDIS_ENABLED=true \
  -e OWNCLOUD_REDIS_HOST=redis \
  --volume owncloud_files:/mnt/data \
  owncloud/server:${OWNCLOUD_VERSION}
docker volume create owncloud_redis

docker run -d \
  --name redis \
  -e REDIS_DATABASES=1 \
  --volume owncloud_redis:/var/lib/redis \
  webhippie/redis:latest

docker volume create owncloud_mysql
docker volume create owncloud_backup

docker run -d \
  --name mariadb \
  -e MARIADB_ROOT_PASSWORD=owncloud \
  -e MARIADB_USERNAME=owncloud \
  -e MARIADB_PASSWORD=owncloud \
  -e MARIADB_DATABASE=owncloud \
  --volume owncloud_mysql:/var/lib/mysql \
  --volume owncloud_backup:/var/lib/backup \
  webhippie/mariadb:latest


cat /root/owncloud/toppath.conf

TODO: change port to 7080 and 7443 or whatever

<VirtualHost *:80>
  ServerAdmin webmaster@localhost
  DocumentRoot /var/www/owncloud

TODO: don't chown because it's wrong

# cat 25-chown.sh
#!/usr/bin/env bash

if [[ ${OWNCLOUD_SKIP_CHOWN} == "true" ]]
then
  echo "Skipping chown as requested..."
else
  echo "Fixing base perms..."
  find /var/www/owncloud \( \! -user www-data -o \! -group www-data \) -print0 | xargs -r -0 chown www-data:www-data


OWNCLOUD_DB_HOST setup on different port

  "mysql")

    if ! grep -q ":" <<<${OWNCLOUD_DB_HOST}
    then
      OWNCLOUD_DB_HOST=${OWNCLOUD_DB_HOST}:3306
    fi


odocker.io/library/redis:3.2.11

permissions of /srv/owncloud_redis,owncloud_mariadb, does not need 711 because mount will be sufficient
/srv/owncloud

useradd -d /srv/

OWNCLOUD_SKIP_CHOWN=true
OWNCLOUD_DB_HOST=localhost

OWNCLOUD_REDIS_ENABLED=true
OWNCLOUD_REDIS_HOST=localhost
OWNCLOUD_REDIS_PORT=999
OWNCLOUD_REDIS_PASSWORD=whatever
# don't need this
#OWNCLOUD_REDIS_DB=whatever

pass in ENV REDIS_OPTS to set port

redis:x:101:102:redis:/var/lib/redis:/bin/false
118d0c17c714:/etc/entrypoint.d# grep redis /etc/group
grep redis /etc/group
redis:x:102:redis

# on boot, remove:

/etc/s6/redis/setup

processes have to start as root


rm -f /etc/s6/redis/setup
-e REDIS_DATABASES=1 -e REDIS_PROTECTED=true -e REDIS_OPTS='--bind 127.0.0.1'

vagrant can be user
