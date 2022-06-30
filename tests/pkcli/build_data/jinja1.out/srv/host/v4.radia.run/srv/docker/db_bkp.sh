#!/bin/bash
# Abuse of db_bkp, because really just "nightly"
docker rmi $(docker images --filter dangling=true -q || true) >& /dev/null || true
