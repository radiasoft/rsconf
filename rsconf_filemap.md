src/radiasoft/rsconf:
## build-perl-rpms.sh // builds bivio-perl and Bivio (WHY) ??
## container-conf
    - build.sh // clones pykern rsconf and download into ~/src/radiasoft, then if setup.py can be read run the install
    - nginx.conf // config for nginx server the vm’s pull their config trees from
## docs
    - index.rst // ??
    - _static // ??
    - _templates // ??
## etc
    - empty-rpm.sh // ??
## LICENSE // apache license
## MANIFEST.in // adds additional files to the source distribution
## proprietary
    - myapp-dev.tar.gz // ??
## README.md // brief RSConf description and links to the wiki
## requirements.txt // necessary packages required to run the project
## rpm
    - bivio-perl-dev.rpm // ??
    - perl-Bivio-dev.rpm // ??
## rsconf
    - base_pkconfig.py // “default config” ??
    - !!! component // contains python scripts for every component in rsconf (nginx, bkp, base…)
    - db.py // database py script, creates host and T class, defines db functions
    - __init__.py // typical file, lets Python interpreter know directory contains code for Python module
    - !!! package_data // contains data for components (jinja templates, scripts)
    - pkcli
        - build.py // script to build host tree
        - host.py // “host manipulation”, checks for hosts in rsconf_db and returns/initizes them ??
        - __init__.py // typical file, lets Python interpreter know directory contains code for Python module
        - __pycache__ // standard compiled bytecode from python run
        - setup_dev.py // “test tree” ??
        - tls.py // “SSL cert operations”, contains functions to generate certs (signed, self)+ csr’s + keys, verify + read certs ??
    - __pycache__ // standard compiled bytecode from python run
    - rsconf_console.py // “Front-end command line for :mod:`rsconf`”, returns rsconf module from pykern.pkcli, exit if __name__ == “__main__??
    - systemd.py // “create systemd files” + runtime directories
## rsconf.egg-info // standard project adjacent metadata egg
    - dependency_links.txt // URL’s depended on for web pages and direct downloads
    - entry_points.txt // contains entry points for setup
    - PKG-INFO // contains the project’s standard metadata
    - requires.txt // necessary packages required to run the project
    - SOURCES.txt // list of files/packages included in the project, no runtime use
    - top_level.txt // lsat of top level project packages, used at runtime to avoid importing already existing packages
## run
    - db
        - 000.yml // master config file used when setting up a vm
        - local
            - default
                - etc
                    - base.rsconf // just says “default” ??
                    - default.rsconf // just says “default” ??
                - should-ignore~ // should be ignored ??
            - dev
                - 000.sh.jinja // sets install access and location if docker component found ??
                - etc
                    - base.rsconf
                    - dev.rsconf
            - v3.radia.run
                - etc
                    - base.rsconf
                    - dev.rsconf
        - resource
            - dovecot
                - db_bkp.sh.jinja // prints “test override”
        - secret
            - 000.yml // contains private information (passwords, tokens, security configs)
            - 001.yml // contains SSH keys for rsconf and bkp
            - dev
                - mpi_worker
                    - vagrant // contains host and identity (open)ssh keys
                - jupyterhub_proxy_auth	 // key
                - jupyterhub_cookie_secret // key
                - sirepo_jupyterhub_proxy_auth // key
                - sirepo_cookie_private_key // key
                - sirepo_job_server_secret // key
                - sirepo_jupyterhub_cookie_secret // key
            - tls // keys + certs for hosts, host tools (star, jupyter, redirect3), google
            - docker_registry_passwd // encrypted key
            - docker_registry_http_secret // key
            - docker_registry_passwd.json // keys
            - rsconf_auth // encrypted keys
            - rsconf_auth.json // key 
            - postfix_host_sasl_password.json // keys
            - setup_dev.sh // run by setup.dev, installs keys (rpm, ssh)
            - v3.radia.run // keys + certs docker_tls
            - v4.radia.run // keys + certs for docker_tls (job_supervisor, jupyterhub)
            - v5.radia.run // keys + certs docker_tls
            - v6.radia.run // keys + certs docker_tls
            - v9.radia.run // keys + certs for docker_tls (job_supervisor, jupyterhub), dovecot passwords
    - etc
        - bivio-named.pl // initializes conf values (hostmaster, refresh, ipv4 zone…)??
        - secondary_setup.sh // mounts secondary_copy_d, sets true
    - nginx
        - client_body_temp // empty 
        - fastcgi_temp // empty
        - nginx.conf // usual nginx conf
        - nginx.pid // 5-digit pid
        - proxy_temp // empty
        - scgi_temp // empty
        - !!! start.sh // checks for /src/yum, links /src/yum + /radiasoft/…/index.sh to rsconf, kills running nginx pid, starts nginx server
        - uwsgi_temp // empty
    - proprietary
        - myapp-dev.tar.gz // ??
    - rpm
        - bivio-perl-dev.rpm // ??
        - perl-Bivio-dev.rpm // ??
    - srv
        - biviosoftware
            - home-env // ?? GO THROUGH THIS
        - host // contains setup scripts for hosts v3-v9 (000, base, docker, nginx…) GO THROUGH THIS
        - index.html // used when curling from radiasoft depots, find repos in radiasoft directory (/download/installers, repos w/ radiasoft-download.sh)
        - index.sh // checks if github is the install server, links to the github index.sh, runs it
        - radiasoft // contains radiasoft repositories (containers, download, pykern, rsconf)
        - rsconf.sh // contains the rsconf functions (append, install, service_restart… ) GO THROUGH THIS
        - v3.radia.run-netrc // login + initialization + command for curling back into the server
        - v4.radia.run-netrc // login + initialization + command for curling back into the server
        - v5.radia.run-netrc // login + initialization + command for curling back into the server
        - v6.radia.run-netrc // login + initialization + command for curling back into the server
        - v9.radia.run-netrc // login + initialization + command for curling back into the server
        - yum
            - fedora // contains empty radiasoft.repo and 32/x86_64/dev repo data ??
    - srv-tmp
        - host-old // contains setup scripts for old hosts v3-v9 (000, base, docker, nginx…) ??
    - tmp
        - contains private information 000.yml+001.yml (ssh keys, passswords, tokens) and component data json’s for hosts v3-v9
## setup.py // rsconf setup script, imports and executes pksetup.setup with necessary parameters
## tests
    - conftest.py // used to avoid a plugin dependency issue
    - pkcli
        - build_data // data for testing build
            - 1-jinja.in // build data 
            - 1-jinja.out // build trees for v3-v9 hosts
            - 2-fconf.in // build data
            - 2-fconf.out // build trees for v3-v9 hosts
        - build_test.py // test for rsconf build
    - systemd_test.py // test for systemd