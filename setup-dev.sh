#!/bin/bash
#
;# Setup an nginx server or just do this:
#
# cd ~/src
# ln -s ~/src/radiasoft/download/bin/index.sh ~/src/index.html
# python -m SimpleHTTPServer 8000
#
set -e
mkdir -p run/srv/pub
test -L ~/src/index.html || ln -s ~/src/radiasoft/download/bin/index.sh ~/src/index.html
ln -s ~/src run/srv/pub
cat > run/nginx.conf <<'EOF'
worker_processes auto;
# append info or debug
error_log /dev/stderr debug;
pid nginx.pid;
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    client_body_temp_path client_body_temp;
    proxy_temp_path proxy_temp;
    fastcgi_temp_path fastcgi_temp;
    uwsgi_temp_path uwsgi_temp;
    scgi_temp_path scgi_temp;
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
        '$status $body_bytes_sent "$http_referer" '
        '"$http_user_agent" "$http_x_forwarded_for"';
    access_log /dev/stdout main;
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen 8000 default_server;
        server_name  _;
        root /usr/share/nginx/html;

        error_page 404 /404.html;
        location = /40x.html {
        }

        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
        }

        location / {
            root srv;
            #auth_basic "*";
            #auth_basic_user_file passwd;
            try_files /$remote_user$uri /$remote_user$uri/index.html /pub$uri pub/$uri/index.html =404;
        }
    }
}
EOF

# You'll still get an error about /var/log/nginx/error.log, dumb...
# daemon off could be in the file
/usr/sbin/nginx -p "$PWD/run" -g "daemon off;" -c nginx.conf
