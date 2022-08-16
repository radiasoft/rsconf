#!/bin/bash
nfs_server_rsconf_component() {
rsconf_yum_install nfs-utils
rsconf_service_prepare 'nfs-server' '/etc/exports.d' '/etc/sysconfig/nfs'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/exports.d/srv_mpi_worker_user.exports' '508cd0405e8ee18aec97ecc29e7bde27'
rsconf_install_file '/etc/exports.d/srv_sirepo_db_user.exports' '2def7dd26be91dfd40fd0ed27c5d7373'
rsconf_edit_no_change_res=0 rsconf_edit $'/etc/sysconfig/nfs' $'^RPCNFSDCOUNT=16$' $'s<^#?\\s*RPCNFSDCOUNT.*><RPCNFSDCOUNT=16>'
rsconf_service_restart
}
