# -*- coding: utf-8 -*-
u"""create filebeat configuration
:copyright: NA
:license: NA
"""

from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from rsconf import component
from pykern import pkio
from pathlib import Path

class T(component.T):

    def internal_build(self): # ?? difference between internal_build and internal_build_compile
        self.buildt.require_component('base_all') # componants generally need base_all

        # print to test component is being touched
        self.append_root_bash('echo "Filebeat touched"')

        # download + install public signing key
        self.append_root_bash('sudo rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch')

        # move elastic.repo file into /etc/yum.repos.d
        path = Path('/etc/yum.repos.d/elastic.repo') # ?? should check for repo in python or bash script
        if path.is_file():
            self.append_root_bash('echo Elastic Yum Repo: Found by Filebeat')
        else: 
            self.append_root_bash('echo Elastic Yum Repo: Moving by Filebeat')
            self.append_root_bash('mv /home/vagrant/src/radiasoft/rsconf/rsconf/package_data/filebeat/elastic.repo /etc/yum.repos.d')

        # yum install
        self.append_root_bash('rsconf_yum_install filebeat')
        
        # enable start on boot
        self.append_root_bash('sudo systemctl enable filebeat')
        
        # print finished initial install
        self.append_root_bash('echo "Filebeat P1 Complete: Initial Install"')

# Edit/replace filebeat.yml config
# - Connect to Elasticsearch

# Enable desired modules for shipping
# sudo filebeat modules enable nginx

# Edit module config in module.d
# - Change all “false”s to “true”s

# Setup Filebeat
# sudo filebeat setup -e

# Start Filebeat
# sudo systemctl start filebeat
