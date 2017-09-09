### rsconf

RadiaSoft host configuration

Learn more at https://github.com/radiasoft/rsconf.

Documentation: http://rsconf.readthedocs.org/en/latest/

#### Debugging


https://stackoverflow.com/a/24830777/3075806
```sh
# grep nginx /var/log/audit/audit.log | grep denied | audit2allow -M mynginx
******************** IMPORTANT ***********************
To make this policy package active, execute:

semodule -i mynginx.pp
```

#### License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
