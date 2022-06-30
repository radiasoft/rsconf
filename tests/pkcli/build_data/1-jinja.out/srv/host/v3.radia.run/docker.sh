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
rsconf_install_file '/etc/docker/daemon.json' 'a17ec19008bd0b099e7537e419a3f6ef'
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
rsconf_install_file '/srv/docker/db_bkp.sh' '1c83cb791e6f8ad7e3506a08f56c6c41'
rsconf_install_access '700' 'root' 'root'
rsconf_install_directory '/srv/docker/db_bkp'
}
#!/bin/bash

docker_install() {
    local dir=/srv/docker/volumes
    if [[ -e $dir && $(type -t docker) != '' ]]; then
#TODO(robnagler) update docker rpm?
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
            https://download.docker.com/linux/fedora/docker-ce.repo
    else
        yum-config-manager \
            --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum makecache fast
        # yum-plugin-ovl required for overlay2 on centos7
        # https://github.com/docker-library/official-images/issues/1291
        rsconf_yum_install yum-plugin-ovl
    fi
#TODO(robnagler) how to update?
    rsconf_yum_install docker-ce
        # Give vagrant user access in dev mode only
        usermod -aG docker vagrant
}

docker_main() {
    docker_install
}
