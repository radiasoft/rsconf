# -*- coding: utf-8 -*-
u"""create elasticsearch configuration
:copyright: NA
:license: NA
"""
import os
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from rsconf import component
from pykern import pkio
from pathlib import Path
from jinja2 import FileSystemLoader, Environment

# helper function for rendering elasticsearch config
def render_config(host_name, host_ip, host_port):
    template_dir = "/home/vagrant/src/radiasoft/rsconf/rsconf/package_data/elasticsearch"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("elasticsearch.yml.jinja")
    return template.render(host_name=host_name, host_ip=host_ip, host_port=host_port)
    
# helper function for creating elasticsearch API command for creating a user
def create_user(username, password, roles, full_name, email):
    template_dir = "/home/vagrant/src/radiasoft/rsconf/rsconf/package_data/elasticsearch"
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("user_request.txt.jinja")
    return template.render(username=username, password=password, roles=roles, full_name=full_name, email=email)

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
        path = Path('/etc/yum.repos.d/elastic.repo')
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
        
        # start Elasticsearch service
        self.append_root_bash('sudo service elasticsearch start')
        
        # TODO: generate new super-user password and save to 'secret', still need to trim file
        self.append_root_bash('sudo /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic > /home/vagrant/src/radiasoft/rsconf/rsconf/package_data/elasticsearch/master_password.txt')
        
        # generate bash command for ship-only Filebeat user and run
        generate_user = create_user("shipperNode", "very-secure-password", "beats_system", "Filebeat Shipper", "bernerakownt@gmail.com")
        self.append_root_bash(generate_user)
        
        # generate new elasticsearch config and write it to package_data before replacing existing YAML
        generated_config = render_config(host_name="NAME", host_ip="ADDRESS", host_port="PORT")
        file = open("/home/vagrant/src/radiasoft/rsconf/rsconf/package_data/elasticsearch/elasticsearch.yml", "w")
        file.write(generated_config)
        file.close()
        self.append_root_bash("sudo cat /home/vagrant/src/radiasoft/rsconf/rsconf/package_data/elasticsearch/elasticsearch.yml > /etc/elasticsearch/elasticsearch.yml")