# rsconf

Under development.

## Master

On the master as dev user start

```sh
curl radia.run | bash -s vagrant-centos7 v3.radia.run
vssh
sudo su -
curl radia.run | bash -s redhat-base
curl radia.run | bash -s home
yum install -y nginx
exit
curl radia.run | bash -s home
. ~/.bashrc
bivio_pyenv_2
mkdir -p ~/src/radiasoft
cd ~/src/radiasoft
gcl download
gcl pykern
cd pykern
pip install -e .
cd ..
gcl rsconf
cd rsconf
pip install -e .
rm -rf run; rsconf build
bash run/nginx/start.sh
```

On the master as root:

```bash
sudo su -
export host=v3.radia.run install_channel=dev install_server=http://v3.radia.run:8000
curl "$install_server" | bash -s rsconf.sh "$host" setup_dev
exit
exit
vagrant reload
vssh
# NOTE: restart nginx like above (do not "rsconf build")
sudo su -
export install_channel=dev install_server=http://v3.radia.run:8000
curl "$install_server" | bash -s rsconf.sh "$(hostname -f)" setup_dev
```

On the client, create a test.sh file and run it:

```bash
mkdir ~/v4
cd ~/v4
cat > test.sh <<'END'
#!/bin/bash
. ~/.bashrc
set -e -x
export host=v4.radia.run install_server=http://v3.radia.run:8000 install_channel=dev
curl radia.run | bash -s vagrant-centos7 "$host" "$(dig +short "$host")"
vssh sudo su - <<EOF
export install_channel=dev install_server="$install_server"
# fails because of reboot
curl "$install_server" | bash -s rsconf.sh "$host" setup_dev || true
EOF
vagrant reload
vssh sudo su - <<EOF
set -e -x
export install_channel=$install_channel install_server=$install_server
curl "$install_server" | bash -s rsconf.sh "$host" setup_dev
# postresql restart request
curl "$install_server" | bash -s rsconf.sh "$host" setup_dev
EOF
END
bash test.sh
```

You'll need to destroy manually.

## License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
