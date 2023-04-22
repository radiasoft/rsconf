#!/bin/bash
wordpress_rsconf_component() {
rsconf_service_prepare 'wordpress' '/etc/systemd/system/wordpress.service' '/etc/systemd/system/wordpress.service.d' '/srv/wordpress'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/wordpress'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/wordpress/cmd' '397e0b4a6f29053265227040f2bacf99'
rsconf_install_file '/srv/wordpress/env' '22e03a134cc868bb12094d8dc118a6c4'
rsconf_install_file '/srv/wordpress/remove' '1cbfc83e4897d3066eb99f0896783529'
rsconf_install_file '/srv/wordpress/start' 'f34ef13182a58f7f112978d70b2f81ca'
rsconf_install_file '/srv/wordpress/stop' 'caf8a0561e27cd390f9ed76095b704a9'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/wordpress.service' '836ef3c39fd8781c57812a8409d954b2'
rsconf_service_docker_pull 'docker.io/radiasoft/wordpress:dev' 'wordpress' 'wordpress' ''
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/wordpress/log'
rsconf_install_directory '/srv/wordpress/srv'
rsconf_install_directory '/srv/wordpress/srv/wp1.v4.radia.run'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/wordpress/envvars' '7af4bfc2d049d033019cda2cd95ef2e8'
rsconf_install_file '/srv/wordpress/apache.conf' 'ed8f74d9db7c1107e4f90c871d132434'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/wordpress/run' '133a178458fa52b5914c30f8f070bf07'
rsconf_install_file '/srv/wordpress/reload' '910131df768ca8cf21cf7f63f9dc64fb'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/logrotate.d/wordpress' '36e73f44b5811d1aaa5fdd07e874522e'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/nginx/conf.d/wp1.v4.radia.run.conf' '44eb9550504aac8da4b31b89d41c7d02'
wordpress_main
}
#!/bin/bash

wordpress_init() {
    local db=$1
    local user=$2
    local pw=$3
    rs_mariadb_init "$db" "$user" "$pw"
    curl -L -s -S https://wordpress.org/latest.tar.gz | tar xzf -
    mv wordpress/* .
    rmdir wordpress
    # Only really used for testing
    rm -f wp-config-sample.php
    cat <<'EOF' > .htaccess
RewriteEngine On
RewriteBase /
RewriteRule ^index\.php$ - [L]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule . /index.php [L]
EOF
    (
        cat <<EOF
<?php
define('DB_NAME', '$db');
define('DB_USER', '$user');
define('DB_PASSWORD', '$pw');
define('DB_HOST', '127.0.0.1:7011');
define('DB_CHARSET', 'utf8');
define('DB_COLLATE', '');
EOF
        curl -L -s -S https://api.wordpress.org/secret-key/1.1/salt/
        cat <<'EOF'
$table_prefix  = 'wp_';
define('WP_DEBUG', false);
if ( !defined('ABSPATH') )
	define('ABSPATH', dirname(__FILE__) . '/');
require_once(ABSPATH . 'wp-settings.php');
EOF
    ) > wp-config.php
    chown -R 'vagrant:vagrant' .
}

wordpress_main() {
        if [[ ! -e /srv/wordpress/srv/wp1.v4.radia.run/wp-config.php ]]; then
            (
                cd '/srv/wordpress/srv/wp1.v4.radia.run';
                wordpress_init 'wp1' 'wp1user' 'wp1pass'
            )
        fi

}

