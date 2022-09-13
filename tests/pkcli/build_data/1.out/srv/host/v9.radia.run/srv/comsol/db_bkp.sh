#!/bin/bash
t=/srv/comsol/tmp
shopt -s nullglob
find /srv/comsol/tmp/{*native,*client,csappserver*,csbatch*,fileup*,*/????????} \
     -prune -mtime +7 | xargs -n 100 rm -rf
