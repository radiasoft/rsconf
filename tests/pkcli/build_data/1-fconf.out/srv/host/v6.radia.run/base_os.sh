#!/bin/bash
base_os_rsconf_component() {
rsconf_service_prepare 'systemd-journald' '/etc/systemd/journald.conf.d'
rsconf_service_prepare 'sshd' '/etc/ssh'

rsconf_install_access '700' 'nobody' 'vagrant'
rsconf_install_file '/etc/base.rsconf' '8eec1e97ac602d3228bad33b61efeaae'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/default.rsconf' 'de2b14ae7499f90736fc4a92327553a5'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/dev.rsconf' '8eec1e97ac602d3228bad33b61efeaae'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/etc/systemd/journald.conf.d'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/systemd/journald.conf.d/99-rsconf.conf' '9556d6ace0f4113eed37ec4bb5225de1'
rsconf_install_file '/etc/sysctl.d/60-rsconf-base.conf' 'da732edac738b7aeda84e28eb516c99b'
rsconf_install_file '/etc/ssh/sshd_config' '74e16725821ffa2522ea8b65d6371d6c'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/hostname' 'be2478321c6d2ff6a25488ca14b201c9'
rsconf_install_file '/etc/motd' '6bf408e65fc8387235735f3caebd3593'
base_os_main
}
#!/bin/bash

base_os_chrony() {
    if ! base_os_if_virtual_box; then
        # only needed for VirtualBox
        return
    fi
    systemctl stop chronyd
    systemctl disable chronyd
}

base_os_if_virtual_box() {
    local x=$(dmidecode -s system-product-name 2>/dev/null)
    [[ $x =~ VirtualBox || -f /vagrant/Vagrantfile ]]
}

base_os_journal_persist() {
    # https://unix.stackexchange.com/a/159390
    local d=/var/log/journal
    if [[ -d $d ]]; then
        return
    fi
    rsconf_install_access 700 root root
    rsconf_install_directory "$d"
    systemd-tmpfiles --create --prefix "$d"
    rsconf_service_trigger_restart systemd-journald
}

base_os_logical_volume() {
    local name=$1 gigabytes=$2 vg=$3 mount_d=$4 mode=$5
    local dev="/dev/mapper/$vg-$name"
    local x=$(lvs --units g --no-headings -o lv_size "$dev" 2>/dev/null)
    if ! grep -s -q "^$dev " /etc/fstab; then
        rsconf_edit_no_change_res=0 rsconf_append /etc/fstab "^$dev " "$dev $mount_d xfs defaults 0 0"
    fi
    if [[ $x =~ ([0-9]+)(\.[0-9]+)?g ]]; then
        local actual=${BASH_REMATCH[1]}
        # Account for the truncation and a little slop
        if (( $actual + 2 >= $gigabytes )); then
            return
        fi
        # -y: wipe signatures
        lvextend -y -L "${gigabytes}G" "$dev"
        # xfs_group requires a mounted file system
        if ! mountpoint "$mount_d"; then
            mount "$mount_d"
        fi
        xfs_growfs "$dev"
        return
    fi
    lvcreate -y --wipesignatures y -L "${gigabytes}G" -n "$name" "$vg"
    mkfs -t xfs -n ftype=1 "$dev"
    # the component that sets mount_d will set the permissions and owner
    mkdir -p "$mount_d"
    mount "$mount_d"
    chmod "$mode" "$mount_d"
}

base_os_logical_volumes() {
    : this line is just in case base_os.logical_volume_cmds is empty
    
}

base_os_main() {
    rsconf_radia_run_as_user root redhat-base
    rsconf_append_authorized_key 'root' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIIB3mhGsrxFV4KnHjDtBaaU7ZdlNhwxIEPZ3/+Bv1xZY v3.radia.run'
    if [[ ! -d /srv ]]; then
        mkdir -p /srv
        chmod 755 /srv
    fi
    local reboot=
    if base_os_ipv4; then
        reboot=1
    fi
#TODO(robnagler) consider permissive on back end and enforcing on front end
    if rsconf_edit /etc/selinux/config ^SELINUX=disabled \
        's{(?<=^SELINUX=).*}{disabled}'; then
        reboot=1
    fi
    base_os_chrony
    base_os_journal_persist
    rsconf_edit_no_change_res=0 rsconf_append /etc/screenrc 'escape ^^^^'
    base_os_logical_volumes
    if [[ $reboot ]]; then
        rsconf_reboot
    fi
}

base_os_ipv4() {
    local i= no_reboot=1
    if [[ -e /proc/sys/net/ipv6/conf/all/disable_ipv6 ]]; then
        i=$(sysctl -n net.ipv6.conf.all.disable_ipv6)
        if [[ ! $i ]]; then
            install_err 'sysctl net.ipv6.conf.all.disable_ipv6: failed'
        fi
    else
        # Once disabled at the kernel init level, you can't query net.ipv6 at all
        i=1
    fi
#TODO(robnagler) return result to test install?
    sysctl -q -p --system
    if (( $i == 0 )); then
        # Need to disable ipv6 for rpcbind and Python 3's ssl library seems to want
        # to try ipv6, and if it can't get it, it dies.
        no_reboot=0

        # https://access.redhat.com/solutions/8709
        # Must be done first time
        install_info 'Rebuilding initrd to disable ipv6'
        # Not bothering with backup, because this only happens once after fresh
        # restart.
        sysctl -w net.ipv6.conf.all.disable_ipv6=1 net.ipv6.conf.default.disable_ipv6=1
        dracut -f
    fi
    base_os_postfix
    base_os_rpcbind_patch
    return $no_reboot
}

base_os_postfix() {
    if type postconf >& /dev/null; then
        postconf -e inet_protocols=ipv4
    fi
}

base_os_rpcbind_patch() {
    # Binding to IPv6 address not available since kernel does not support IPv6.
    # https://bugzilla.redhat.com/show_bug.cgi?id=1402961
    local old=/usr/lib/systemd/system/rpcbind.socket
    if [[ ! -e $old ]]; then
        return
    fi
    local new=/etc/systemd/system/rpcbind.socket
    if [[ ! -r "$new" || $old -nt $new ]]; then
        cp -a "$old" "$new"
    fi
    if rsconf_edit "$new" '! BindIPv6Only' 'm{\[::\]:|BindIPv6Only} && ($_=q{})'; then
        systemctl daemon-reload
        rsconf_service_trigger_restart rpcbind.socket
    fi
}

