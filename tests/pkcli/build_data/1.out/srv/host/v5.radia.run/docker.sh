#!/bin/bash
docker_rsconf_component() {
rsconf_service_prepare 'docker' '/etc/systemd/system/docker.service' '/etc/systemd/system/docker.service.d' '/etc/docker'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/etc/docker'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/etc/docker/tls'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/docker/tls/cert.pem' '8b6f398174f7ef8fde6ca00062a02795'
rsconf_install_file '/etc/docker/tls/key.pem' '0c05eefd65658d3bd336c70a385d4e22'
rsconf_install_file '/etc/docker/tls/cacert.pem' '6decfd9aa3b78cb106c38a000343fd62'
rsconf_install_access '400' 'root' 'root'
rsconf_install_file '/etc/docker/daemon.json' '86e11b92e350f6f66f4999077e670660'
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
rsconf_install_file '/root/.docker/config.json' 'c597084dc13c9de30ada16c243efb98c'
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

docker_update() {
    if ! docker_should_update; then
        return;
    fi
    yum makecache fast
    install_yum update "$_docker_pkg" "$_docker_pkg"-cli
    if docker_should_update; then
        install_err "Installed docker=$(docker --version) is still < min_software_version=0.0.0 after update."
    fi
}

docker_install() {
    declare dir=/srv/docker/volumes
    if [[ -e $dir && $(type -t docker) != '' ]]; then
        docker_update
        install_info "$dir: exists, docker already installed"
        return
    fi
    if [[ -e /var/lib/docker ]]; then
        # This will happen on dev systems only, but a good check
        install_err '/var/lib/docker exists:
systemctl stop docker
systemctl disable docker
rm -rf /var/lib/docker/*
umount /var/lib/docker
rmdir /var/lib/docker
perl -pi -e "s{^/var/lib/docker.*}{}" /etc/fstab
lvremove -f /dev/mapper/docker-vps

Then re-run rsconf
'
    fi
#TODO(robnagler) need a list of repos and RPMs.
    # F27
    if rsconf_fedora_release_if 26; then
        # https://docs.docker.com/engine/installation/linux/docker-ce/fedora/#set-up-the-repository
        dnf -y install dnf-plugins-core
        dnf config-manager \
            --add-repo \
            https://download.docker.com/linux/fedora/"$_docker_pkg".repo
    else
        yum-config-manager \
            --add-repo https://download.docker.com/linux/centos/"$_docker_pkg".repo
        yum makecache fast
        # yum-plugin-ovl required for overlay2 on centos7
        # https://github.com/docker-library/official-images/issues/1291
        rsconf_yum_install yum-plugin-ovl
    fi
    rsconf_yum_install "$_docker_pkg"
        # Give vagrant user access in dev mode only
        usermod -aG docker vagrant
    if docker_should_update; then
        install_err "Installed docker=$(docker version) is < min_software_version=0.0.0 after install."
    fi
}

docker_main() {
    docker_install
}

docker_should_update() {
    docker_should_update_do Client || docker_should_update_do Server
}

docker_should_update_do() {
    declare docker_component=$1
    declare i=$(docker version --format="{{ json . }}" | jq --raw-output ".$docker_component.Version")
    (( $(docker_version_num "$i") < $(docker_version_num '0.0.0') ))
}

docker_version_num() {
    declare str=$1
    printf '%d%06d%06d' ${str//./ }

}

