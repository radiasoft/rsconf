# -*- coding: utf-8 -*-
"""

yum install -y tftp-server tftp
chown root:nobody /var/lib/tftpboot
chmod 755 /var/lib/tftpboot
#mkdir /var/lib/tftpboot/upload
#chown nobody:nobody /var/lib/tftpboot/upload
#chmod 700 /var/lib/tftpboot/upload
#cp /usr/lib/systemd/system/tftp.service /etc/systemd/system/tftp.service
# https://linux.die.net/man/8/tftpd
#rsconf_edit ExecStart=/usr/sbin/in.tftpd --umask 555 --create --secure /var/lib/tftpboot
EDITOR=touch systemctl edit --full tftp.socket
perl -pi -e 's/=69/=10.1.2.1:69/' /etc/systemd/system/tftp.socket
systemctl daemon-reload
systemctl enable tftp
systemctl start tftp


cat > /etc/systemd/system/tftp.service <<EOF
[Unit]
Description=Tftp Server
Requires=tftp.socket
Documentation=man:in.tftpd

[Service]
ExecStart=/usr/sbin/in.tftpd -s {{ run_d.db }}
StandardInput=socket

[Install]
Also=tftp.socket
EOF

cat > /etc/systemd/system/tftp.socket <<EOF
[Unit]
Description=Tftp Server Activation Socket
After=network-online.target
Wants=network-online.target

[Socket]
ListenDatagram={{ ip }}:69

[Install]
WantedBy=sockets.target
EOF

:copyright: Copyright (c) 2022 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
