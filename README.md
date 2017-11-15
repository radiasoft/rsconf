# rsconf

Under development.

On the master as dev user:

```bash
cd ~/src/radiasoft/rsconf
pip install -e .
rm -rf run
rsconf build
bash run/nginx/start.sh
```

On the master as root:

```bash
sudo su -
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server/v5.bivio.biz-netrc" > ~/.netrc
chmod 400 ~/.netrc
curl "$install_server" | bash -s rsconf.sh v5.bivio.biz
```

On the client:

```bash
curl radia.run | bash -s vagrant-centos7 v4.bivio.biz 10.10.10.40
vssh
sudo su -
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server/v4.bivio.biz-netrc" > ~/.netrc
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

## License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
