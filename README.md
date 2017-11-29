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
host=v5.bivio.biz
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server/$host-netrc" > ~/.netrc
chmod 400 ~/.netrc
curl "$install_server" | bash -s rsconf.sh "$host"
```

On the client:

```bash
curl radia.run | bash -s vagrant-centos7 "$host" 10.10.10.40
vssh
sudo su -
host=v4.bivio.biz
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server/$host-netrc" > ~/.netrc
chmod 400 ~/.netrc
curl "$install_server" | bash -s rsconf.sh "$host"
exit
exit
vagrant reload
vssh
sudo su -
host=v4.bivio.biz
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server" | bash -s rsconf.sh "$host"
```

## License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
