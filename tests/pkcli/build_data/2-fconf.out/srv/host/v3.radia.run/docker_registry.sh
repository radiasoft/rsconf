#!/bin/bash
docker_registry_rsconf_component() {
rsconf_service_prepare 'docker_registry' '/etc/systemd/system/docker_registry.service' '/etc/systemd/system/docker_registry.service.d' '/srv/docker_registry'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/docker_registry'
rsconf_install_access '500' 'root' 'root'
rsconf_install_file '/srv/docker_registry/env' '22e03a134cc868bb12094d8dc118a6c4'
rsconf_install_file '/srv/docker_registry/remove' 'e665529295ba836559a290eb1b30ec67'
rsconf_install_file '/srv/docker_registry/start' '6c6035cf0ad1302cdf76c158052f2fd8'
rsconf_install_file '/srv/docker_registry/stop' 'c67f4f9793a3877ec1698bb1d019156c'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/docker_registry.service' 'c71da0c1f0921580142b8023a3980b75'
rsconf_service_docker_pull 'docker.io/library/registry:2' 'docker_registry'
rsconf_install_file '/srv/docker_registry/v3.radia.run.key' 'b98bb61f3b76969ee1a259d5a1afd5f1'
rsconf_install_file '/srv/docker_registry/v3.radia.run.crt' '71151618f3ca16bad2d73ef5a6683c1c'
rsconf_install_file '/srv/docker_registry/passwd' 'a84a84a3439553d304e483bbffdca67d'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/docker_registry/db'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/srv/docker_registry/config.yml' '0e9d9315b5fa7a3db6e947e10a42f0b8'
rsconf_service_restart
}
