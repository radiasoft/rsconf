#!/bin/bash
network_rsconf_component() {
rsconf_service_prepare 'network' '/etc/sysconfig/network-scripts' '/etc/resolv.conf'
rsconf_service_prepare 'iptables' '/etc/sysconfig/iptables' '/etc/sysconfig/network-scripts'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/resolv.conf' '96c1279df4e73fe8b9975833dc71321f'
rsconf_install_file '/etc/sysconfig/network-scripts/ifcfg-em1' 'e225a3f7b4b071e5c204b1182c17ab94'
rsconf_install_file '/etc/sysconfig/network-scripts/ifcfg-em2' '4f8c01335a3bf1a8a89ba5d09fdf28df'
rsconf_install_file '/etc/sysconfig/iptables' 'ab5fc0b74fbd3e234c097eea429a0b25'
network_main
}
#!/bin/bash

network_iptables() {
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
    if [[ $(systemctl is-active NetworkManager) == active ]]; then
        systemctl stop NetworkManager
    fi
    systemctl disable NetworkManager >& /dev/null || true
    if [[ $(systemctl is-active firewalld) == active ]]; then
        systemctl stop firewalld
    fi
    systemctl disable firewalld >& /dev/null || true
    systemctl mask firewalld >& /dev/null || true
    network_iptables
}

