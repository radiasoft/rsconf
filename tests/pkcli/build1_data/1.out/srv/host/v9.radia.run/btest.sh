#!/bin/bash
btest_rsconf_component() {
rsconf_service_prepare 'btest.timer' '/etc/systemd/system/btest.service' '/etc/systemd/system/btest.timer' '/srv/btest'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/btest'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/btest/start' '8cf5c4757183681faf4f33629f8fc206'
rsconf_install_access '444' 'root' 'root'
rsconf_install_file '/etc/systemd/system/btest.timer' 'db74bbfe017f3485a2f99dc8dc8a588b'
rsconf_install_file '/etc/systemd/system/btest.service' 'b817e96955920937e11b567bd54e64ca'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/btest/apps'
rsconf_install_directory '/home/vagrant/btest-mail'
rsconf_install_directory '/home/vagrant/btest-mail-copy'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/home/vagrant/.procmailrc' '9cd81f66a63641d775937ce4b1e8c6df'
rsconf_install_access '700' 'vagrant' 'vagrant'
rsconf_install_directory '/srv/btest/apps/petshop'
rsconf_install_directory '/srv/btest/apps/petshop/db'
rsconf_install_directory '/srv/btest/apps/petshop/bkp'
rsconf_install_directory '/srv/btest/apps/petshop/log'
rsconf_install_access '400' 'vagrant' 'vagrant'
rsconf_install_file '/srv/btest/apps/petshop/bivio-unit.bconf' 'cff40b94ff40a56a025861b5939cf9c4'
rsconf_install_file '/srv/btest/apps/petshop/bivio-acceptance.bconf' '1eeac1d87a4a44c5d6210fb74e4914d7'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/btest/apps/petshop/run' 'd9fedc6f639e9bc1d9b11103d98baf1d'
rsconf_install_access '500' 'vagrant' 'vagrant'
rsconf_install_file '/srv/btest/run' '165cabcd57a2586d7476c895407c42a1'
}