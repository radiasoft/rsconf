### rsconf

Under development.

On the master (v5.bivio.biz):

```bash
cd ~/src/radiasoft/rsconf
pip install -e .
rm -rf run
rsconf build
bash run/nginx/start.sh
```

On the client:

```bash
vssh
sudo su -
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server/dev-netrc" > ~/.netrc
chmod 400 ~/.netrc
curl "$install_server" | bash -s rsconf.sh v4.bivio.biz
exit
exit
vagrant reload
vssh
sudo su -
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server" | bash -s rsconf.sh v4.bivio.biz
```

#### License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
