# -*- coding: utf-8 -*-
u"""create postfix configuration

:copyright: Copyright (c) 2017 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""
from __future__ import absolute_import, division, print_function
from pykern import pkio
from rsconf import component

_CONF_D = pkio.py_path('/etc/postfix')

class T(component.T):

    def internal_build(self):
        from rsconf import systemd

        systemd.unit_prepare(self, _CONF_D)
        self.append_root_bash_with_resource(
            'postfix/main.sh',
            self.hdb,
            'postfix_main',
        )

'''
    my($key, $crt) = $func_ssl_crt->('/etc/postfix', undef, 1);
    return
        unless $key && $crt;
    return (
	"${type}_tls_cert_file = $crt",
	"${type}_tls_key_file = $key",
        "${type}_tls_CAfile = /etc/pki/tls/certs/ca-bundle.crt",
        "${type}_tls_security_level = may",
    );
my($func_ssl_crt) = sub {
    my($dir, $owner, $no_create) = @_;
    $owner ||= 'root';
    # COUPLING: "server" is hardwired into postgresql, but not postfix
    my($key, $crt) = map("$dir/server.$_", 'key', 'crt');
    unless (-r $key && -r $crt) {
        if ($no_create) {
            return;
        }
	Util_SSL()->self_signed_crt($CFG->{host_name});
	# Must be a mv, not rename(), because might be different file sys
	system('mv', "$CFG->{host_name}.key", $key);
	system('mv', "$CFG->{host_name}.crt", $crt);
	IO_File()->chown_by_name($owner, $owner, $key, $crt);
	IO_File()->chmod(0600, $key, $crt);
    }
    return ($key, $crt);
};


my($func_postfix_app_setup) = sub {
    $func_postfix_master->([
'smtp      inet  n       -       n       -       200       smtpd',
'local     unix  -       n       n       -       8       local',
"b-sendmail-http  unix  -       n       n       -       2       pipe flags=DRhu user=nobody:nobody argv=$CFG->{sendmail_http} \${client_address} \${recipient} localhost.localdomain:80/_mail_receive/\%s /bin/false any-param",
    ]);
    $func_postfix_main->([
        'mailbox_transport = b-sendmail-http:unix',
        'smtpd_timeout = ${stress?12}${stress:300}',
        'smtpd_hard_error_limit = ${stress?1}${stress:20}',
	'b-sendmail-http_destination_recipient_limit = 1',
	@{$CFG->{postfix_main_extra} || []},
    ]);
    system('newaliases');
    system('service postfix restart');
    return;
};


my($func_postfix_main) = sub {
    my($lines) = @_;
    system(qw(postconf -e), @$lines);
    return;
};

my($func_postfix_master) = sub {
    my($lines) = @_;
    $func_read_write->(
        '/etc/postfix/master.cf',
	sub {
	    my($in) = @_;
	    foreach my $x (@$lines) {
	        my($cfg) = "$x\n";
		my($n) = $cfg =~ /^(\S+)/;
		$$in =~ s/^$n\s.*\n/$cfg/m || ($$in .= $cfg);
	    }
	    return;
	},
    );
    return;
};

my($func_postfix_tls_conf) = sub {
    my($type) = @_;
    my($key, $crt) = $func_ssl_crt->('/etc/postfix', undef, 1);
    return
        unless $key && $crt;
    return (
	"${type}_tls_cert_file = $crt",
	"${type}_tls_key_file = $key",
        "${type}_tls_CAfile = /etc/pki/tls/certs/ca-bundle.crt",
        "${type}_tls_security_level = may",
    );
};
    $func_postfix_main->([
        'alias_maps = hash:/etc/aliases',
        'alias_database = hash:/etc/aliases',
	'inet_interfaces = all',
	'inet_protocols = ipv4',
	'mailbox_command = /usr/bin/procmail -t -Y -a "$EXTENSION" -d "$USER"',
	'recipient_delimiter = +',
	'mydestination = $myhostname, localhost, /etc/mail/local-host-names',
	'local_recipient_maps =',
	'biff = no',
	'smtpd_banner = $myhostname ESMTP',
	'smtpd_delay_reject = no',
        'mynetworks = 127.0.0.0/8',
	'smtpd_sender_restrictions = reject_unauth_pipelining, permit_mynetworks, reject_non_fqdn_sender, reject_unknown_sender_domain',
	'smtpd_recipient_restrictions = reject_unauth_pipelining, permit_mynetworks, reject_unauth_destination, reject_non_fqdn_recipient, reject_unknown_recipient_domain',
	'message_size_limit = 50000000',
	'mailbox_size_limit = 0',
        $func_postfix_tls_conf->('smtp'),
        $func_postfix_tls_conf->('smtpd'),
    ]);


my($func_ssl_crt) = sub {
    my($key, $crt) = $func_ssl_crt->('/etc/postfix', undef, 1);
    return
        unless $key && $crt;
    return (
	"${type}_tls_cert_file = $crt",
	"${type}_tls_key_file = $key",
        "${type}_tls_CAfile = /etc/pki/tls/certs/ca-bundle.crt",
        "${type}_tls_security_level = may",
    );

    my($dir, $owner, $no_create) = @_;
    $owner ||= 'root';
    # COUPLING: "server" is hardwired into postgresql, but not postfix
    my($key, $crt) = map("$dir/server.$_", 'key', 'crt');
    unless (-r $key && -r $crt) {
        if ($no_create) {
            return;
        }
	Util_SSL()->self_signed_crt($CFG->{host_name});
	# Must be a mv, not rename(), because might be different file sys
	system('mv', "$CFG->{host_name}.key", $key);
	system('mv', "$CFG->{host_name}.crt", $crt);
	IO_File()->chown_by_name($owner, $owner, $key, $crt);
	IO_File()->chmod(0600, $key, $crt);
    }
    return ($key, $crt);
};


        systemd.unit_prepare(self, _CONF_D)
        j2_ctx = pkcollections.Dict(self.hdb)
        self.install_access(mode='400', owner=self.hdb.rsconf_db_root_u)
        self.install_resource('nginx/global.conf', j2_ctx, _GLOBAL_CONF)
        systemd.unit_enable(self)
'''
