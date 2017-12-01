yum install -y dhcp
cat > /etc/dhcp/dhcpd.conf <<'EOF'
option domain-name "bivio.biz";
option domain-name-servers 8.8.8.8;
default-lease-time 600;
max-lease-time 7200;
subnet 10.1.5.0 netmask 255.255.255.0 {
  range 10.1.5.200 10.1.5.210;
}
subnet 10.1.2.0 netmask 255.255.255.0 {
  range 10.1.2.200 10.1.2.210;
}
EOF
EDITOR=touch systemctl edit --full dhcpd.service
perl -pi -e '/^ExecStart/ && ! / em1/ && s/$/ em1 em1.5/' /etc/systemd/system/dhcpd.service
systemctl daemon-reload
systemctl enable dhcpd
systemctl start dhcpd
