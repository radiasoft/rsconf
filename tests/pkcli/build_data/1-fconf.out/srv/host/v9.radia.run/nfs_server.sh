#!/bin/bash
nfs_server_rsconf_component() {
rsconf_yum_install nfs-utils
rsconf_service_prepare 'nfs-server' '/etc/exports.d' '/etc/sysconfig/nfs'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/exports.d/exports_foo.exports' 'cacb7e2d24f0ee1de9f5bf0e66b61955'
rsconf_edit_no_change_res=0 rsconf_edit '/etc/sysconfig/nfs' '^RPCNFSDCOUNT=64$' 's<^#?\s*RPCNFSDCOUNT.*><RPCNFSDCOUNT=64>'
rsconf_service_restart
}
