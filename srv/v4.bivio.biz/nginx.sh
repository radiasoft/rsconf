#!/bin/bash
nginx_main() {
    rsconf_require base_users
#TODO(robnagler) upgrade when?
    rsconf_yum_install nginx
    rsconf_install_access 400 root
    rsconf_install etc/nginx/nginx.conf etc/nginx/conf.d/00-default.conf etc/nginx/conf.d/sirepo.conf etc/nginx/conf.d/sirepo.crt etc/nginx/conf.d/sirepo.key
    systemctl daemon-reload
    systemctl start nginx
    systemctl enable nginx
}
