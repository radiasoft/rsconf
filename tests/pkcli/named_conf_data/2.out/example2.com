$TTL 9M
$ORIGIN example2.com.
@ IN SOA ns1.bivio.biz. hostmaster.example.com. ( 2023111502 7M 8M 5M 6M )
@ IN NS ns1.bivio.biz.
@ IN NS ns2.bivio.biz.
20240328._domainkey.dkim IN TXT key4
dkim IN A 1.2.3.3
dkim IN MX 10 dkim
dkim IN TXT key1=abc
no-dkim IN A 1.2.3.3
no-dkim IN MX 10 no-dkim
