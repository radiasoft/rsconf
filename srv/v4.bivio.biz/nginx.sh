#!/bin/bash
nginx_main() {
    rsconf_require base_users
#TODO(robnagler) upgrade when?
    yum install -y nginx
    rsconf_install_access 400 root
    rsconf_install etc/nginx/nginx.conf etc/nginx/conf.d/sirepo.{conf,crt,key}
    systemctl start nginx
    systemctl enable nginx
}
