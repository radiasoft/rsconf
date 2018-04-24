MinSpareServers {{ wordpress.num_servers }}
MaxSpareServers	{{ wordpress.num_servers }}
MaxRequestWorkers {{ wordpress.num_servers }}
MaxConnectionsPerChild   120

# https://blog.chmouel.com/2016/09/22/the-trick-to-get-your-wordpress-behind-a-reverse-proxy/
# https://www.digitalocean.com/community/questions/redirect-loop-with-wordpress-on-apache-with-nginx-reverse-proxy-and-https-on-ubuntu-16

# https://codex.wordpress.org/Changing_The_Site_URL
# Edit functions.php
# If you have access to the site via FTP, then this method will help you quickly get a site back up and running, if you changed those values incorrectly.
#
# 1. FTP to the site, and get a copy of the active theme's functions.php file. You're going to edit it in a simple text editor and upload it back to the site.
#
# 2. Add these two lines to the file, immediately after the initial "<?php" line.
#
# update_option( 'siteurl', 'http://example.com' );
# update_option( 'home', 'http://example.com' );
# Use your own URL instead of example.com, obviously.
#
# 3. Upload the file back to your site, in the same location. FileZilla offers a handy "edit file" function to do all of the above rapidly; if you can use that, do so.
#
# 4. Load the login or admin page a couple of times. The site should come back up.
#
#
# <VirtualHost *:80>
# 	# The ServerName directive sets the request scheme, hostname and port that
# 	# the server uses to identify itself. This is used when creating
# 	# redirection URLs. In the context of virtual hosts, the ServerName
# 	# specifies what hostname must appear in the request's Host: header to
# 	# match this virtual host. For the default virtual host (this file) this
# 	# value is not decisive as it is used as a last resort host regardless.
# 	# However, you must set it for any further virtual host explicitly.
# 	#ServerName www.example.com
#
# 	ServerAdmin webmaster@localhost
# 	DocumentRoot /var/www/html
#
# 	# Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
# 	# error, crit, alert, emerg.
# 	# It is also possible to configure the loglevel for particular
# 	# modules, e.g.
# 	#LogLevel info ssl:warn
#
# 	ErrorLog ${APACHE_LOG_DIR}/error.log
# 	CustomLog ${APACHE_LOG_DIR}/access.log combined
#
# 	# For most configuration files from conf-available/, which are
# 	# enabled or disabled at a global level, it is possible to
# 	# include a line for only one particular virtual host. For example the
# 	# following line enables the CGI configuration for this host only
# 	# after it has been globally disabled with "a2disconf".
# 	#Include conf-available/serve-cgi-bin.conf
# </VirtualHost>
#
#     ServerTokens Min
#
