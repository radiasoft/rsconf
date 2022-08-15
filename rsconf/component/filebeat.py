# -*- coding: utf-8 -*-
u"""create filebeat configuration
:copyright: NA
:license: NA
"""
from ast import AsyncFunctionDef
import os
import stat
from __future__ import absolute_import, division, print_function
from pykern.pkcollections import PKDict
from rsconf import component
from pykern import pkio
from pathlib import Path
from jinja2 import FileSystemLoader, Environment

# helper function for rendering filebeat config
def render_config(hosts, ca_fingerprint, protocol, username, password):
        template_dir = "/home/vagrant/src/radiasoft/rsconf/rsconf/package_data/filebeat"
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("filebeat.yml.jinja")
        return template.render(hosts=hosts, ca_fingerprint=ca_fingerprint, protocol=protocol, username=username, password=password)
    
# helper function to set module configs to true
def edit_module(filepath):
    os.chmod(filepath, stat.S_IRWXU|stat.S_IRWXG|stat.S_IRWXO)
    with open(filepath) as f:
        s = f.read()
        if "false" not in s:
            return
    with open(filepath, 'w') as f:
        s = s.replace("false", "true")
        f.write(s)

class T(component.T):
    def internal_build(self): # ?? difference between internal_build and internal_build_compile
        self.buildt.require_component('base_all') # componants generally need base_all

        # print to test component is being touched
        self.append_root_bash('echo "Filebeat touched"')

        # download + install public signing key
        self.append_root_bash('sudo rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch')

        # move elastic.repo file into /etc/yum.repos.d
        path = Path('/etc/yum.repos.d/elastic.repo')
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
        
        # generate new filebeat config and replace old one
        generated_config = render_config(hosts="HOSTS", fingerprint="FINGERPRINT", protocol="PROTOCOL", username="USERNAME", password="PASSWORD")
        file = open("/home/vagrant/src/radiasoft/rsconf/rsconf/package_data/filebeat/filebeat.yml", "w")
        file.write(generated_config)
        file.close()
        self.append_root_bash("sudo cat /home/vagrant/src/radiasoft/rsconf/rsconf/package_data/filebeat/filebeat.yml > /etc/filebeat/filebeat.yml")
        
        # Enable desired modules for shipping
        modules = ["nginx"]
        for i in modules:
            enable_cmd = "sudo filebeat modules enable " + i
            self.append_root_bash(enable_cmd)
        
        # Set module filesets to true in config
        for j in modules:
            filepath = "/etc/filebeat/modules.d/" + j + ".yml.disabled"
            edit_module(filepath)
        
        # setup Filebeat
        self.append_root_bash("sudo filebeat setup -e")
        
        # start filebeat
        self.append_root_bash("sudo systemctl start filebeat")