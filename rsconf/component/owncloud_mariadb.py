cat run
#!/bin/bash

if [ -f ./setup ]
then
  source ./setup
fi

STARTCMD="/usr/bin/mysqld_safe"

if [ ! -d "/var/lib/mysql/mysql" ]
then
  if [ -z "${MARIADB_ROOT_PASSWORD}" ]
  then
    echo >&2 "Error: Database is uninitialized and MARIADB_ROOT_PASSWORD not set"
    /bin/s6-svscanctl -t /etc/s6
    exit 1
  fi

  echo "Running mysql_install_db..."
  mysql_install_db --user=mysql --datadir="/var/lib/mysql"
  echo "Finished mysql_install_db"

  INIT_FILE="/tmp/mariadb-boot.sql"

  echo "" >| ${INIT_FILE}
  echo "DELETE FROM mysql.user;" >> ${INIT_FILE}
  echo "CREATE USER 'root'@'%' IDENTIFIED BY '${MARIADB_ROOT_PASSWORD}';" >> ${INIT_FILE}
  echo "GRANT ALL ON *.* TO 'root'@'%' WITH GRANT OPTION;" >> ${INIT_FILE}
  echo "DROP DATABASE IF EXISTS test;" >> ${INIT_FILE}
  echo "FLUSH PRIVILEGES;" >> ${INIT_FILE}

  if [[ -n "${MARIADB_USERNAME}" && -n "${MARIADB_DATABASE}" ]]
  then
    echo "CREATE DATABASE IF NOT EXISTS \`${MARIADB_USERNAME}\`;" >> ${INIT_FILE}
    echo "GRANT ALL PRIVILEGES ON \`${MARIADB_DATABASE}\`.* TO '${MARIADB_USERNAME}'@'%' IDENTIFIED BY '${MARIADB_PASSWORD}';" >> ${INIT_FILE}
    echo "FLUSH PRIVILEGES;" >> ${INIT_FILE}
  fi

  if [[ -n "${MARIADB_USERNAME}" && -z "${MARIADB_DATABASE}" ]]
  then
    echo "CREATE DATABASE IF NOT EXISTS \`${MARIADB_USERNAME}\`;" >> ${INIT_FILE}
    echo "GRANT ALL PRIVILEGES ON \`${MARIADB_USERNAME}\`.* TO '${MARIADB_USERNAME}'@'%' IDENTIFIED BY '${MARIADB_PASSWORD}';" >> ${INIT_FILE}
    echo "FLUSH PRIVILEGES;" >> ${INIT_FILE}
  fi

  STARTCMD="${STARTCMD} --init-file=${INIT_FILE}"
fi

exec ${STARTCMD}
# cat setup
#!/bin/bash

declare -x MARIADB_DEFAULT_CHARACTER_SET
declare -x MARIADB_CHARACTER_SET_SERVER
declare -x MARIADB_COLLATION_SERVER
declare -x MARIADB_KEY_BUFFER_SIZE
declare -x MARIADB_MAX_ALLOWED_PACKET
declare -x MARIADB_TABLE_OPEN_CACHE
declare -x MARIADB_SORT_BUFFER_SIZE
declare -x MARIADB_NET_BUFFER_SIZE
declare -x MARIADB_READ_BUFFER_SIZE
declare -x MARIADB_READ_RND_BUFFER_SIZE
declare -x MARIADB_MYISAM_SORT_BUFFER_SIZE
declare -x MARIADB_LOG_BIN
declare -x MARIADB_BINLOG_FORMAT
declare -x MARIADB_SERVER_ID
declare -x MARIADB_INNODB_DATA_FILE_PATH
declare -x MARIADB_INNODB_BUFFER_POOL_SIZE
declare -x MARIADB_INNODB_LOG_FILE_SIZE
declare -x MARIADB_INNODB_LOG_BUFFER_SIZE
declare -x MARIADB_INNODB_FLUSH_LOG_AT_TRX_COMMIT
declare -x MARIADB_INNODB_LOCK_WAIT_TIMEOUT
declare -x MARIADB_INNODB_USE_NATIVE_AIO
declare -x MARIADB_INNODB_LARGE_PREFIX
declare -x MARIADB_INNODB_FILE_FORMAT
declare -x MARIADB_INNODB_FILE_PER_TABLE

declare -x MARIADB_MAX_ALLOWED_PACKET
declare -x MARIADB_KEY_BUFFER_SIZE
declare -x MARIADB_SORT_BUFFER_SIZE
declare -x MARIADB_READ_BUFFER
declare -x MARIADB_WRITE_BUFFER

[[ -z "${MARIADB_DEFAULT_CHARACTER_SET}" ]] && MARIADB_DEFAULT_CHARACTER_SET="utf8"
[[ -z "${MARIADB_CHARACTER_SET_SERVER}" ]] && MARIADB_CHARACTER_SET_SERVER="utf8"
[[ -z "${MARIADB_COLLATION_SERVER}" ]] && MARIADB_COLLATION_SERVER="utf8_general_ci"
[[ -z "${MARIADB_KEY_BUFFER_SIZE}" ]] && MARIADB_KEY_BUFFER_SIZE="16M"
[[ -z "${MARIADB_MAX_ALLOWED_PACKET}" ]] && MARIADB_MAX_ALLOWED_PACKET="1M"
[[ -z "${MARIADB_TABLE_OPEN_CACHE}" ]] && MARIADB_TABLE_OPEN_CACHE="64"
[[ -z "${MARIADB_SORT_BUFFER_SIZE}" ]] && MARIADB_SORT_BUFFER_SIZE="512K"
[[ -z "${MARIADB_NET_BUFFER_SIZE}" ]] && MARIADB_NET_BUFFER_SIZE="8K"
[[ -z "${MARIADB_READ_BUFFER_SIZE}" ]] && MARIADB_READ_BUFFER_SIZE="256K"
[[ -z "${MARIADB_READ_RND_BUFFER_SIZE}" ]] && MARIADB_READ_RND_BUFFER_SIZE="512K"
[[ -z "${MARIADB_MYISAM_SORT_BUFFER_SIZE}" ]] && MARIADB_MYISAM_SORT_BUFFER_SIZE="8M"
[[ -z "${MARIADB_LOG_BIN}" ]] && MARIADB_LOG_BIN="mysql-bin"
[[ -z "${MARIADB_BINLOG_FORMAT}" ]] && MARIADB_BINLOG_FORMAT="mixed"
[[ -z "${MARIADB_SERVER_ID}" ]] && MARIADB_SERVER_ID="1"
[[ -z "${MARIADB_INNODB_DATA_FILE_PATH}" ]] && MARIADB_INNODB_DATA_FILE_PATH="ibdata1:10M:autoextend"
[[ -z "${MARIADB_INNODB_BUFFER_POOL_SIZE}" ]] && MARIADB_INNODB_BUFFER_POOL_SIZE="16M"
[[ -z "${MARIADB_INNODB_LOG_FILE_SIZE}" ]] && MARIADB_INNODB_LOG_FILE_SIZE="5M"
[[ -z "${MARIADB_INNODB_LOG_BUFFER_SIZE}" ]] && MARIADB_INNODB_LOG_BUFFER_SIZE="8M"
[[ -z "${MARIADB_INNODB_FLUSH_LOG_AT_TRX_COMMIT}" ]] && MARIADB_INNODB_FLUSH_LOG_AT_TRX_COMMIT="1"
[[ -z "${MARIADB_INNODB_LOCK_WAIT_TIMEOUT}" ]] && MARIADB_INNODB_LOCK_WAIT_TIMEOUT="50"
[[ -z "${MARIADB_INNODB_USE_NATIVE_AIO}" ]] && MARIADB_INNODB_USE_NATIVE_AIO="1"
[[ -z "${MARIADB_INNODB_LARGE_PREFIX}" ]] && MARIADB_INNODB_LARGE_PREFIX="OFF"
nngn[[ -z "${MARIADB_INNODB_FILE_FORMAT}" ]] && MARIADB_INNODB_FILE_FORMAT="Antelope"
[[ -z "${MARIADB_INNODB_FILE_PER_TABLE}" ]] && MARIADB_INNODB_FILE_PER_TABLE="ON"
[[ -z "${MARIADB_MAX_ALLOWED_PACKET}" ]] && MARIADB_MAX_ALLOWED_PACKET="16M"
[[ -z "${MARIADB_KEY_BUFFER_SIZE}" ]] && MARIADB_KEY_BUFFER_SIZE="20M"
[[ -z "${MARIADB_SORT_BUFFER_SIZE}" ]] && MARIADB_SORT_BUFFER_SIZE="20M"
[[ -z "${MARIADB_READ_BUFFER}" ]] && MARIADB_READ_BUFFER="2M"
[[ -z "${MARIADB_WRITE_BUFFER}" ]] && MARIADB_WRITE_BUFFER="2M"

/usr/bin/templater -d -p mariadb \
  -o /etc/mysql/my.cnf \
  /etc/templates/my.cnf.tmpl

if [[ $? -ne 0 ]]
then
  /bin/s6-svscanctl -t /etc/s6
fi

chown -R mysql:mysql \
  /var/lib/mysql
# rpm -qf /usr/bin/templater
bash: rpm: command not found
# ls -al /usr/bin/templater
-rwxr-xr-x    1 root     root       8607968 Mar 29 06:13 /usr/bin/templater
# ls -l /etc/templates/my.cnf.tmpl
-rw-r--r--    1 root     root          2042 Mar 29 07:19 /etc/templates/my.cnf.tmpl
# cat !$
cat /etc/templates/my.cnf.tmpl
[client]
port = 3306
socket = /run/mysqld/mysqld.sock

default-character-set = {{ envString "DEFAULT_CHARACTER_SET" }}

[mysqld]
port = 3306
socket = /run/mysqld/mysqld.sock

character-set-server = {{ envString "CHARACTER_SET_SERVER" }}
collation-server = {{ envString "COLLATION_SERVER" }}

skip-external-locking
key_buffer_size = {{ envString "KEY_BUFFER_SIZE" }}
max_allowed_packet = {{ envString "MAX_ALLOWED_PACKET" }}
table_open_cache = {{ envString "TABLE_OPEN_CACHE" }}
sort_buffer_size = {{ envString "SORT_BUFFER_SIZE" }}
net_buffer_length = {{ envString "NET_BUFFER_SIZE" }}
read_buffer_size = {{ envString "READ_BUFFER_SIZE" }}
read_rnd_buffer_size = {{ envString "READ_RND_BUFFER_SIZE" }}
myisam_sort_buffer_size = {{ envString "MYISAM_SORT_BUFFER_SIZE" }}

tmpdir = /tmp

log-bin = {{ envString "LOG_BIN" }}
binlog_format = {{ envString "BINLOG_FORMAT" }}

server-id = {{ envString "SERVER_ID" }}

innodb_data_home_dir = /var/lib/mysql
innodb_data_file_path = {{ envString "INNODB_DATA_FILE_PATH" }}
innodb_log_group_home_dir = /var/lib/mysql
innodb_buffer_pool_size = {{ envString "INNODB_BUFFER_POOL_SIZE" }}
innodb_log_file_size = {{ envString "INNODB_LOG_FILE_SIZE" }}
innodb_log_buffer_size = {{ envString "INNODB_LOG_BUFFER_SIZE" }}
innodb_flush_log_at_trx_commit = {{ envString "INNODB_FLUSH_LOG_AT_TRX_COMMIT" }}
innodb_lock_wait_timeout = {{ envString "INNODB_LOCK_WAIT_TIMEOUT" }}
innodb_use_native_aio = {{ envString "INNODB_USE_NATIVE_AIO" }}

innodb_large_prefix = {{ envString "INNODB_LARGE_PREFIX" }}
innodb_file_format = {{ envString "INNODB_FILE_FORMAT" }}
innodb_file_per_table = {{ envString "INNODB_FILE_PER_TABLE" }}

[mysqldump]
quick
quote-names
max_allowed_packet = {{ envString "MAX_ALLOWED_PACKET" }}

[mysql]
no-auto-rehash

[myisamchk]
key_buffer_size = {{ envString "KEY_BUFFER_SIZE" }}
sort_buffer_size = {{ envString "SORT_BUFFER_SIZE" }}
read_buffer = {{ envString "READ_BUFFER" }}
write_buffer = {{ envString "WRITE_BUFFER" }}

[mysqlhotcopy]
interactive-timeout

!includedir /etc/mysql/conf.d/
# ls /etc/mysql/conf.d
# p
