# -*- coding: utf-8 -*-
"""?

# https://www.unixmen.com/install-pxe-server-centos-7/
# https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/installation_guide/chap-installation-server-setup
yum install -y syslinux nfs-utils

lvcreate -L 10G -n netboot centos
mkfs.xfs /dev/mapper/centos-netboot
echo '/dev/mapper/centos-netboot /var/lib/netboot xfs defaults 0 0' >> /etc/fstab
mount /var/lib/netboot
chmod 755 /var/lib/netboot
echo '/var/lib/netboot 10.1.5.0/24(ro,all_squash) 10.1.2.0/24(ro,all_squash)' >> /etc/exports
exportfs /var/lib/netboot

Now save the following as /var/lib/tftpboot/pxelinux.cfg/default:
  next-server 192.168.0.199; #  DHCP server ip
  filename "pxelinux.0";


mkdir -p /var/lib/tftpboot/pxelinux.cfg
mkdir /var/lib/tftpboot/pxelinux
# Maybe needs to be different, ie centos7/
cp /usr/share/syslinux/* /var/lib/tftpboot/*

server=10.1.2.1

cat > /var/lib/tftpboot/pxelinux.cfg/default << EOF
default menu.c32
prompt 1
timeout 15
menu title centos7

label centos7
    menu label centos7
    kernel /centos7/vmlinuz
    append initrd=/centos7/initrd.img inst.repo=nfs:10.1.2.1:/var/lib/netboot/CentOS-7-x86_64-DVD-1708.iso inst.ks=nfs:10.1.2.1:/var/lib/netboot/centos7-ks.cfg ip=dhcp
EOF

mv CentOS-7-x86_64-DVD-1708.iso /var/lib/netboot
cp centos7-ks.cfg /var/lib/netboot
#mount -t loopback,ro CentOS-7-x86_64-DVD-1708.iso centos7

mount -t loopback,ro /var/lib/netboot/CentOS-7-x86_64-DVD-1708.iso /var/lib/centos7

mkdir /var/lib/tftpboot/centos7
cp centos7/images/pxeboot/* /var/lib/tftpboot/centos7
umount centos7
chmod -R a+rX /var/lib/netboot /var/lib/tftpboot
mount -t loopback,ro CentOS-7-x86_64-DVD-1708.iso centos7
bash: syntax error near unexpected token `}'
[py2;@v5 pkgs]$ cat > /dev/null
  616  ls /var/lib/netboot/centos7
  617  ls -al /var/lib/netboot
  618  umount /var/lib/netboot/centos7
  619  chmod 755 /var/lib/netboot/centos7
  620  mount -t loopback,ro CentOS-7-x86_64-DVD-1708.iso centos7
  621  ls centos7
  622  ls -altr
  623  umount /var/lib/netboot/centos7
  624  mkdir /var/lib/centos7
  625  chmod 755 /var/lib/centos7
  626  mount -t loopback,ro /var/lib/netboot/CentOS-7-x86_64-DVD-1708.iso centos7 /var/lib/centos7
  627  ls /var/lib
  628  h
  629  mount -t loopback,ro /var/lib/netboot/CentOS-7-x86_64-DVD-1708.iso /var/lib/centos7
  630  exportfs -a
  631  exportfs -v
  632  df
  633  ls /var/lib/netboot/


cat > /etc/dhcp/dhcpd.conf <<'EOF'
max-lease-time 7200;
allow booting;

subnet 10.1.5.0 netmask 255.255.255.0 {
  allow bootp;
  range 10.1.5.200 10.1.5.210;
  option routers 10.1.5.1;
  next-server 10.1.2.1;
  filename "/pxelinux.0";
}
subnet 10.1.2.0 netmask 255.255.255.0 {
  allow bootp;
  range 10.1.2.200 10.1.2.210;
  option routers 10.1.2.1;
  next-server 10.1.2.1;
  filename "/pxelinux.0";
}
# blocked networks
subnet 192.168.2.0 netmask 255.255.255.0 {
}
subnet 217.17.132.32 netmask 255.255.255.224 {
}
subnet 10.1.3.0 netmask 255.255.255.0 {
}
subnet 10.1.4.0 netmask 255.255.255.0 {
}
subnet 10.1.6.0 netmask 255.255.255.0 {
}
EOF

:copyright: Copyright (c) 2022 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
