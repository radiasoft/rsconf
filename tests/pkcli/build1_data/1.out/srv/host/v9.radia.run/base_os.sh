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
rsconf_install_file '/etc/security/limits.d/99-rsconf.conf' '0e2ee6a80d800ef63084be31e954bbaa'
rsconf_service_prepare 'reboot' '/etc/security/limits.d/99-rsconf.conf'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/hostname' '20e1de3282fcdf4a1e3df4993b0fecfb'
rsconf_install_file '/etc/motd' '6bf408e65fc8387235735f3caebd3593'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/yum.repos.d/duosecurity.repo' '71f539dd52ce623cd071b497b617f2b2'
rsconf_install_rpm_key 'gpg-pubkey-ff696172-62979e51'
rsconf_yum_install duo_unix
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/duo/pam_duo.conf' '5717fc698953812c8f9e86bb674d33bd'
rsconf_install_file '/etc/pam.d/sshd' '0e1c42ba763cb8eaae0275aea35b7c16'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/ssh/sshd_config' '384d4b70bfed0a0c7f29223c3be309c0'
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
    base_os_postfix
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
    base_os_pwquality
    base_os_rpcbind_patch
    return $no_reboot
}

base_os_postfix() {
    if ! type postconf >& /dev/null; then
        return
    fi
    if [[ ! $(postconf inet_protocols) =~ inet_protocols.?=.?ipv4 ]]; then
        postconf -e inet_protocols=ipv4
        rsconf_service_restart_at_end postfix
    fi
    if rsconf_edit /etc/postfix/master.cf '^smtp\s.*inet.*smtpd' 's/^#(?=smtp\s.*inet.*smtpd)//'; then
        rsconf_service_restart_at_end postfix
    fi
}

base_os_pwquality() {
    rsconf_edit_no_change_res=0 rsconf_edit /etc/security/pwquality.conf 'minlen=16' 's/^#?\s*minlen.*/minlen=16/'
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

