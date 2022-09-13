#!/bin/bash
nfs_client_rsconf_component() {
nfs_client_main
}
#!/bin/bash

# https://serverfault.com/a/810229
# /etc/systemd/system/teamd@.service.d/override.conf
# may be an issue with network manager not being used

nfs_client_add() {
    local fs=$1
    local mount=$2
    # https://www.ibm.com/support/knowledgecenter/en/SSEQVQ_8.1.2/client/c_bac_nfshsmounts.html
    # https://wiki.archlinux.org/index.php/NFS#Mount_using_.2Fetc.2Ffstab
    # May want to add: noatime,nodiratime; We aren't using ACLs
    # relatime is there by default on RH. rsize and wsize are large by default, too
    local options=defaults,vers=4.1,soft,noacl,_netdev
    rsconf_install_access 700 root root
    rsconf_install_mount_point "$mount"
    # Technically can mount $fs twice so what we want to ensure is $mount is not twice
    rsconf_edit_no_change_res=0 rsconf_append /etc/fstab "[[:space:]]$mount[[:space:]]" "$fs $mount nfs $options 0 0"
    # https://stackoverflow.com/a/460061/3075806
    if [[ $(stat -f -L -c %T "$mount" 2>/dev/null || true) != nfs ]]; then
        mount "$mount"
        rsconf_service_file_changed "$mount"
    fi
}

nfs_client_main() {
    rsconf_yum_install nfs-utils
    nfs_client_add 'v4.radia.run:/srv/sirepo/db/users' '/srv/sirepo/db/users'

}

