$TTL 9M
$ORIGIN example.com.
@ IN SOA ns1.bivio.biz. hostmaster.example.com. ( 2023111502 7M 8M 5M 6M )
@ IN NS ns1.bivio.biz.
@ IN NS ns2.bivio.biz.
alias IN CNAME example.other.com.
back IN A 192.168.182.16
back IN MX 10 back
back IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
dict1 IN A 111.22.33.27
dict1 IN MX 10 mail
dict1 IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
example.com. IN A 111.22.33.24
example.com. IN MX 10 mail
example.com. IN MX 20 mail.other.com.
example.com. IN TXT "v=spf1 a mx include:aspmx.googlemail.com include:mail.yahoo.com -all"
ftp IN CNAME www
key1 IN TXT value1
key2 IN TXT value2
mail IN A 111.22.33.24
mail IN MX 10 mail
mail IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
ns1 IN A 111.22.33.24
ns1 IN MX 10 ns1
ns1 IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
ns2 IN A 111.22.33.25
ns2 IN MX 10 ns2
ns2 IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
ski IN A 10.10.1.1
ski IN MX 10 ski
ski IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
two.level IN A 111.22.33.26
two.level IN MX 10 two.level
two.level IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
www IN A 111.22.33.25
www IN MX 10 www
www IN TXT "v=spf1 a mx include:aspmx.googlemail.com -all"
