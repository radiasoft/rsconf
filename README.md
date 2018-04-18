# rsconf

This is a pre-alpha machine configuration management system which can be tested
in a Vagrant environemnt and deployed on VMs or bare metal (with minimal OS installed).

Some of the design goals are:

* Program in programming languages
* Fail fast with debuggable context
* Trust the master but not the clients
* Configure in as few YAML files as possible
* High-level opinions baked in (CentOS 7, docker started via systemd, etc.)
* Build everything on the master first and download with Curl/Bash
* Generate secrets automatically and persistently
* Pull from client; push via ssh (if desired/configured)
* No builtin "update all" except via shell (`for host in`)
* Single master serving dev/alpha/beta/prod channels (stages)
* Updates to files, container images, etc. cause server restarts in proper order
* Serverless so master can be bootstraped using curl file://
* Client requirements: bash and yum
* Server requirements: nginx, python, pykern

# Development

To configure the initial master in Vagrant on a Mac or a Linux development environment:

```sh
radia_run vagrant-centos7 v3.radia.run
vssh
bivio_pyenv_2
set -euo pipefail
sudo yum install -y nginx
mkdir -p ~/src/radiasoft
cd ~/src/radiasoft
gcl download
gcl containers
gcl pykern
cd pykern
pip install -e .
cd ..
gcl rsconf
cd rsconf
pip install -e .
rsconf build
```

On the master as root:

```bash
sudo su -
export host=v3.radia.run install_channel=dev install_server=file:///home/vagrant/src/radiasoft/rsconf/run/srv
curl "$install_server/index.html" | bash -s rsconf.sh "$host" setup_dev
exit
exit
vagrant reload
vssh
sudo su -
export install_channel=dev install_server=file:///home/vagrant/src/radiasoft/rsconf/run/srv
curl "$install_server/index.html" | bash -s rsconf.sh "$(hostname -f)" setup_dev
```

On the master as dev user:

```bash
# so usermod takes effect
logout
vssh
cd ~/src/radiasoft/rsconf
bash run/nginx/start.sh &
export install_channel=dev install_server=http://v3.radia.run:2916
cd ~/src/biviosoftware
gcl rpm-perl
gcl container-perl
cd container-perl
git pull
radia_run container-build
cd ~/src/radiasoft/rsconf
mkdir -p rpm
rpm_perl_install_dir=$PWD/rpm radia_run biviosoftware/rpm-perl bivio-perl
rpm_perl_install_dir=$PWD/rpm radia_run biviosoftware/rpm-perl Bivio
```

On the client, create a test.sh file and run it:

```bash
mkdir ~/v4
cd ~/v4
cat > test.sh <<'END'
#!/bin/bash
. ~/.bashrc
set -euxo pipefail
export host=v4.radia.run install_server=http://v3.radia.run:2916 install_channel=dev
radia_run vagrant-centos7 "$host" "$(dig +short "$host")"
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
EOF
END
bash test.sh
```

You'll need to destroy manually.

## License

License: http://www.apache.org/licenses/LICENSE-2.0.html

Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
