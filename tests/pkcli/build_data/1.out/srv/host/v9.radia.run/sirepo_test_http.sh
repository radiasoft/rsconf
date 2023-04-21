#!/bin/bash
sirepo_test_http_rsconf_component() {
rsconf_service_prepare 'sirepo_test_http.timer' '/etc/systemd/system/sirepo_test_http.service' '/etc/systemd/system/sirepo_test_http.timer' '/srv/sirepo_test_http'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_test_http'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_test_http/cmd' '7ecc6c7e7ffbb674fb7432c18b2f388f'
rsconf_install_file '/srv/sirepo_test_http/env' 'a13c1a0681b072b394d0c603e74f129b'
rsconf_install_file '/srv/sirepo_test_http/remove' '22a2a757831d8bdf1d179aba1bb0dee2'
rsconf_install_file '/srv/sirepo_test_http/start' '96d628bb3200cae331d19a327d92b0bb'
rsconf_install_file '/srv/sirepo_test_http/stop' '5f62d31d91595ef45358da63e97325b1'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_test_http.timer' 'd3e913a370c879e26ebf554d2a28bd3f'
rsconf_install_file '/etc/systemd/system/sirepo_test_http.service' '588fa9f65804bbcb21b9b4f4ec8e97e5'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo_test_http' 'sirepo_test_http' ''
}
