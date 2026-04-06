$TTL 9M
$ORIGIN example2.com.
@ IN SOA ns1.bivio.biz. hostmaster.example.com. ( 2023111502 7M 8M 5M 6M )
@ IN NS ns1.bivio.biz.
@ IN NS ns2.bivio.biz.
@ IN TXT key1=abc
@ IN TXT key2=123
net1.27 IN A 111.22.33.27
net1.27 IN MX 10 net1.27
net1.27 IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
net2-27 IN A 2.3.4.27
net2-27 IN MX 10 net2-27
net2-27 IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
net2-28 IN A 2.3.4.28
net2-28 IN MX 10 net2-28
net2-28 IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
