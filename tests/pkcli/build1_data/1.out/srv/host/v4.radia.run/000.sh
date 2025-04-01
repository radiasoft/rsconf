#!/bin/bash
rsconf_setup_vars 'dev' 'centos' '7'
rsconf_require base_os
rsconf_require network
rsconf_require base_users
rsconf_require logrotate
rsconf_require base_all
rsconf_require postgrey
rsconf_require spamd
rsconf_require postfix
rsconf_require nfs_server
rsconf_require db_bkp
rsconf_require docker
rsconf_require nginx
rsconf_require raydata_scan_monitor
rsconf_require sirepo_jupyterhub
rsconf_require sirepo_job_supervisor
rsconf_require sirepo
rsconf_require script
