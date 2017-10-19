yum install -y tftp-server tftp
chown root:nobody /var/lib/tftpboot
chmod 750 /var/lib/tftpboot
mkdir /var/lib/tftpboot/upload
chown nobody:nobody /var/lib/tftpboot/upload
chmod 700 /var/lib/tftpboot/upload
cp /usr/lib/systemd/system/tftp.service /etc/systemd/system/tftp.service
# https://linux.die.net/man/8/tftpd
rsconf_edit ExecStart=/usr/sbin/in.tftpd --umask 555 --create --secure /var/lib/tftpboot
systemctl daemon-reload
systemctl enable tftp
systemctl start tftp
