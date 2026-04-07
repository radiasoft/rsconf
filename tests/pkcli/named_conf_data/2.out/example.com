$TTL 9M
$ORIGIN example.com.
@ IN SOA ns1.bivio.biz. hostmaster.example.com. ( 2023111502 7M 8M 5M 6M )
@ IN NS ns1.bivio.biz.
@ IN NS ns2.bivio.biz.
20240328._domainkey IN TXT old key1
20240429._domainkey IN TXT "v=DKIM1; k=rsa; " "p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA4H9UesDWFWbnr2OCRcvmpB7l0YbnTzn7Cu4jufbifTushykN8mmkSZqu/aNfZSWruj/awGRv/8ge6povbj7prILu0n3PeStjvIQBz05XKjssGPsLzYw6sX8AQpJqAD4EB671AY8oWl9bl5rAUmILbKuCiXGSilPpsAei80AK3wZK7y5OWy0bW2WmQdusvR/NRa63JdTyC1Uk/n" "2wce4EJCsk2WwP3eeGGp7J7bAThGXYX8LrVwb9Oc2PLMhlnWKThOyxvST5sury/+ickLMqwnBN0z7Mi27TwZcfN34hBJvJdc4bfizUBbK+TJiHrU9XIWEI4Sf5Z3j3CAjdOELAnQIDAQAB"
20240429._domainkey.dkim IN TXT key2
20240429._domainkey.dkim.multi.level IN TXT key3
dkim IN A 1.2.3.1
dkim IN MX 10 dkim
dkim.multi.level IN A 1.2.3.1
dkim.multi.level IN MX 10 dkim.multi.level
example.com. IN A 1.2.3.2
example.com. IN MX 10 example.com.
example.com. IN TXT "v=spf1 a mx 1.2.3.10 -all"
no-dkim IN A 1.2.3.1
no-dkim IN MX 10 no-dkim
