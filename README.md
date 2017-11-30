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
curl "$install_server" | bash -s rsconf.sh "$host" setup_dev
exit
exit
vagrant reload
vssh
# NOTE: restart nginx like above (do not "rsconf build")
sudo su -
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server" | bash -s rsconf.sh "$(hostname -f)"
```

On the client:

```bash
host=v4.bivio.biz
curl radia.run | bash -s vagrant-centos7 "$host" 10.10.10.40
vssh
sudo su -
host=v4.bivio.biz
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server" | bash -s rsconf.sh "$host" setup_dev
exit
exit
vagrant reload
vssh
sudo su -
export install_channel=dev install_server=http://v5.bivio.biz:8000
curl "$install_server" | bash -s rsconf.sh "$(hostname -f)"
```

## License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
