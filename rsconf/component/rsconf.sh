#!/bin/bash
umask 022
curl radia.run | bash -s redhat-base
yum update -y
reboot
yum install -y dhcp nginx tftp tftp-server iptables-services nfs-utils
lvcreate -L 100G -n srv centos
echo '/dev/mapper/centos-srv /srv xfs defaults 0 0' >> /etc/fstab
mount /srv
chmod 755 /srv
systemctl stop NetworkManager
systemctl disable NetworkManager
curl radia.run | bash -s home
. ~/.bashrc
systemctl status tftp
mkdir /srv/tftp
chmod 755 /srv/tftp
mkdir /srv/kickstart
chmod 755 /srv/kickstart
systemctl enable tftp

cp -a /usr/lib/systemd/system/tftp.service /etc/systemd/system/tftp.service
perl -pi -e 's{/var/lib/tftpboot}{/srv/tftp}' /etc/systemd/system/tftp.service
cat > /etc/systemd/system/tftp.socket <<'EOF'
[Unit]
Description=Tftp Server Activation Socket
After=network-online.target
Wants=network-online.target

[Socket]
ListenDatagram=10.1.2.1:69

[Install]
WantedBy=sockets.target
EOF
systemctl daemon-reload
systemctl enable tftp

cat > /etc/systemd/system/dhcpd.service <<'EOF'
[Unit]
Description=DHCPv4 Server Daemon
Documentation=man:dhcpd(8) man:dhcpd.conf(5)
Wants=network-online.target
After=network-online.target
After=time-sync.target

[Service]
Type=notify
ExecStart=/usr/sbin/dhcpd -f -cf /etc/dhcp/dhcpd.conf -user dhcpd -group dhcpd --no-pid em1 em1.5

[Install]
WantedBy=multi-user.target
EOF

emacs /etc/dhcp/dhcpd.conf
systemctl daemon-reload
systemctl enable dhcpd
systemctl start dhcpd

cat >> /etc/exports <<'EOF'
/srv/kickstart 10.1.5.0/24(ro,all_squash) 10.1.2.0/24(ro,all_squash)
EOF
exportfs -av
systemctl start nfs-server

bivio_pyenv_2
cd ~/src
mkdir radiasoft
cd radiasoft
gcl pykern
cd pykern
pip install -e .
cd ..
gcl rsconf
cd rsconf
pip install -e .
(
    umask 077
    mkdir /srv/rsconf/{db/secret,srv}
    chmod 711 /srv/rsconf
    chgrp nginx /srv/rsconf/srv
)
cat >> ~/.post_bivio_bashrc <<'EOF'
export PYKERN_PKCONFIG_CHANNEL=alpha
export RSCONF_DB_ROOT_D=/srv/rsconf
EOF



# extend /var
lvextend -L +125G /dev/vgdata/lvdata
xfs_growfs /mount/point -D size
