#!/bin/bash
sirepo_test_http_rsconf_component() {
rsconf_service_prepare 'sirepo_test_http.timer' '/etc/systemd/system/sirepo_test_http.service' '/etc/systemd/system/sirepo_test_http.timer' '/srv/sirepo_test_http'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/sirepo_test_http'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/sirepo_test_http/cmd' '7ecc6c7e7ffbb674fb7432c18b2f388f'
rsconf_install_file '/srv/sirepo_test_http/env' 'a13c1a0681b072b394d0c603e74f129b'
rsconf_install_file '/srv/sirepo_test_http/remove' 'c82b28125aa7032a88b7014d5c376465'
rsconf_install_file '/srv/sirepo_test_http/start' '7eaa584b48aa78f6fa834279e2ac3378'
rsconf_install_file '/srv/sirepo_test_http/stop' 'c8fe54e779f0d1f322182ba82f7e102e'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/sirepo_test_http.timer' 'd3e913a370c879e26ebf554d2a28bd3f'
rsconf_install_file '/etc/systemd/system/sirepo_test_http.service' 'aaa5ab624e2280ab31c0e54414c685c4'
rsconf_service_docker_pull 'v3.radia.run:5000/radiasoft/sirepo:dev' 'sirepo_test_http'
}
