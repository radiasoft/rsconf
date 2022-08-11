# -*- coding: utf-8 -*-
u"""create elasticsearch configuration
:copyright: NA
:license: NA
"""

from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from rsconf import component
from pykern import pkio
from pathlib import Path

class T(component.T):

    def internal_build(self): # Difference between internal_build and internal_build_compile ??
        self.buildt.require_component('base_all') # componants generally need base_all

        # print to test component is being touched
        self.append_root_bash('echo "Elasticsearch touched"')
        
        # install/update java jdk
        self.append_root_bash('rsconf_yum_install java-1.8.0-openjdk')
        
        # download + install public signing key
        self.append_root_bash('sudo rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch')
        
        # move elastic.repo file into /etc/yum.repos.d
        path = Path('/etc/yum.repos.d/elastic.repo') # should check for repo in python or bash script ??
        if path.is_file():
            self.append_root_bash('echo Elastic Yum Repo: Found by Elasticsearch')
        else: 
            self.append_root_bash('echo Elastic Yum Repo: Moving by Elasticsearch')
            self.append_root_bash('mv /home/vagrant/src/radiasoft/rsconf/rsconf/package_data/elasticsearch/elastic.repo /etc/yum.repos.d')
            
        # clear yum cache and ready metadata for needed repos, pointless step ??
        self.append_root_bash('sudo yum clean all')
        self.append_root_bash('sudo yum makecache')
        
        # yum install
        self.append_root_bash('rsconf_yum_install elasticsearch')
        
        # enable start on boot
        self.append_root_bash('sudo systemctl enable elasticsearch.service')
        
        # print finished initial install
        self.append_root_bash('echo "Elasticsearch P1 Complete: Initial Install"')
        
        # Start Elasticsearch service
        self.append_root_bash('sudo service elasticsearch start')
        
        # generate new super-user password and save to 'secret'
        self.append_root_bash('sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic > /home/vagrant/src/radiasoft/rsconf/rsconf/package_data/elasticsearch/master_password.txt')
        
        # TODO: trim super-user password file
        
        # TODO: replace elasticsearch config with one generated from template
        self.append_root_bash('cat /copy/file/name /target/file/name')

# Edit/replace elasticsearch.yml config
# - Change network host
# - Change http port