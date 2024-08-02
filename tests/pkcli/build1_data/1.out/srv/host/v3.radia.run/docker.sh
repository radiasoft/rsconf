#!/bin/bash
docker_rsconf_component() {
rsconf_service_prepare 'docker' '/etc/systemd/system/docker.service' '/etc/systemd/system/docker.service.d' '/etc/docker'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/etc/docker'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/etc/docker/tls'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/docker/tls/cert.pem' 'be911961627129b5e2c1dac9b077a6e1'
rsconf_install_file '/etc/docker/tls/key.pem' '36c0d4dbda180b3958bad9b3690a9928'
rsconf_install_file '/etc/docker/tls/cacert.pem' '3181d70a9de32d71daa0781bba0fadfb'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/docker/daemon.json' 'bed867d5ead929ffcd50819794f50fc9'
docker_main
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/etc/docker/certs.d'
rsconf_install_directory '/etc/docker/certs.d/v3.radia.run:5000'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/docker/certs.d/v3.radia.run:5000/ca.crt' '71151618f3ca16bad2d73ef5a6683c1c'
rsconf_install_file '/etc/pki/ca-trust/source/anchors/v3.radia.run.crt' '71151618f3ca16bad2d73ef5a6683c1c'
update-ca-trust
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/root/.docker'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/root/.docker/config.json' '8a2ce71534be44e74197f780e8c800b8'
rsconf_install_access '755' 'root' 'root'
rsconf_install_directory '/etc/systemd/system/docker.service.d'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/docker.service.d/99-rsconf.conf' 'b0781f1cabcf1ef79449e4b3d22edc44'
rsconf_service_restart
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/srv/docker/db_bkp.sh' 'c29baf48eb49a688f08990281071d8f5'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/docker/db_bkp'
}
#!/bin/bash
_docker_pkg=docker-ce

docker_main() {
    declare d=/srv/docker/volumes
    if [[ -e $d ]] && type docker >& /dev/null; then
        if docker_up_to_date; then
            install_info "$d: exists, docker already installed"
        else
            # Need to specify cli explicitly or it won't update
            install_yum update "$_docker_pkg" "$_docker_pkg"-cli
        fi
    else
        rsconf_radia_run_as_user root redhat-docker
    fi
    if ! docker_up_to_date; then
        install_err "Installed docker=$(docker_version) is < min_software_version=1.0.0 after install."
    fi
}

docker_up_to_date() {
    declare v=$(docker_version)
    if [[ ! $v ]]; then
        install_err "docker --version did not output a valid version number"
    fi
    printf "%s\n%s\n" '1.0.0' "$v" | sort --version-sort --check &> /dev/null
}

docker_version() {
    if [[ $(docker --version) =~ ([0-9]+\.[0-9]+\.[0-9]+) ]]; then
        echo "${BASH_REMATCH[1]}"
    fi
}

