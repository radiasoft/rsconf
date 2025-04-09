#!/bin/bash
network_rsconf_component() {
rsconf_service_prepare 'NetworkManager' '/etc/NetworkManager/system-connections'
rsconf_service_prepare 'iptables' '/etc/sysconfig/iptables' '/etc/NetworkManager/system-connections'
rsconf_install_access '444' 'root' 'root'
rsconf_install_access '600' 'root' 'root'
rsconf_install_file '/etc/NetworkManager/system-connections/eth0.nmconnection' 'd6f338c3e799fe69154d2d21d0104783'
rsconf_install_file '/etc/NetworkManager/system-connections/eth1.nmconnection' 'ac97fadc1027c3c569999db2d3048a57'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/sysconfig/iptables' 'c37b29b17e21479ffac43b7829d24f4a'
network_main
}
#!/bin/bash

network_firewalld_disable() {
    if [[ $(systemctl is-active firewalld) == active ]]; then
        systemctl stop firewalld
    fi
    systemctl disable firewalld >& /dev/null || true
    systemctl mask firewalld >& /dev/null || true
}

network_iptables_enable() {
    if [[ $(systemctl is-active iptables 2>&1 || true) == active ]]; then
        # Just in case, make sure enabled
        systemctl enable iptables
        return
    fi
    rsconf_yum_install iptables-services
    if [[ ${rsconf_service_no_restart:-} ]]; then
        return
    fi
    systemctl enable iptables
    systemctl start iptables
}

network_main() {
    network_firewalld_disable
    network_manager_enable; network_iptables_enable
}

network_manager_disable() {
    if [[ $(systemctl is-active NetworkManager) == active ]]; then
        systemctl stop NetworkManager
    fi
    systemctl disable NetworkManager >& /dev/null || true
}

network_manager_enable() {
    rsconf_yum_install NetworkManager
    # enable happens in rsconf_systemctl
}

rsconf_systemctl_restart_NetworkManager() {
    nmcli connection reload
    nmcli device reapply eth0
    nmcli device reapply eth1
}

