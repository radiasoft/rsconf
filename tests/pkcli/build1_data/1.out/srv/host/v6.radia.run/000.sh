#!/bin/bash
rsconf_setup_vars 'dev' 'centos' '7'
rsconf_require base_os
rsconf_require network
rsconf_require base_users
rsconf_require logrotate
rsconf_require base_all
rsconf_require db_bkp
rsconf_require docker
rsconf_require nfs_client
rsconf_require mpi_worker
