#!/bin/bash
# Abuse of db_bkp, because really just "nightly"
# Written this way so easier to copy as a one-liner for ad hoc use
docker rm $(docker ps -a -f status=exited -f status=created -q || true) &> /dev/null || true
docker rmi $(docker images --filter dangling=true -q || true) &> /dev/null || true
