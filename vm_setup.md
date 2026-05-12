## purpose

setup current vm for root to serve rsconf to itself using nginx and
setup sirepo with docker on the current vm.

## background

The current user (vagrant) has a python development environment. This
will be the basis for root on the vm's python environment. Since this
is a vagrant vm, sudo works without a password so we can execute sudo
commands.

/srv/rsconf is where the rsconf service should run out of. the rsconf
component can be configured with this so that it generates an rsconf
file for this host. the rsconf primary/master host should be
localhost.localdomain.

sirepo will run
