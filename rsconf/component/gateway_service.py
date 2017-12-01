systemctl stop firewalld >& /dev/null || true
systemctl disable firewalld >& /dev/null || true
yum install -y iptables-services >& /dev/null || true
systemctl enable iptables
systemctl start iptables
#https://www.karlrupp.net/en/computer/nat_tutorial
#https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/4/html/Security_Guide/s1-firewall-ipt-fwd.html
external=em.132
internal=em1
iptables -t nat -A POSTROUTING -o $external -j MASQUERADE
iptables -A FORWARD -i $external -o $internal -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $internal -o $external -j ACCEPT
/usr/libexec/iptables/iptables.init save
