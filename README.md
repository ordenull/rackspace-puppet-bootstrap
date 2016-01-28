# rackspace-puppet-bootstrap
A tool to bootstrap RackSpace servers and connect them to RackConnect and Puppet.

##Usage

This tool requires that the RackSpace API credentials are passed via environmental
variables. In Linux they can be set using the following commands.

	export RACKSPACE_USERNAME=change-me
	export RACKSPACE_APIKEY=1b2b3c4d5e111change-me111f1b2b3c4d5e6f

The following parameters can be passed. Most are required, and some are optional.

### Command line parameters

#### Positional parameters
  * <hostname> *- Fully qualified domain name of the new server.*

#### General parameters
  * --region *- RackSpace region to use [ord|iad|dfw], **[OPTIONAL]**, if ommited will default to **ord***
  * --image *-The UUID of the image to use. **[OPTIONAL]**, if ommited latest "Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)" will be chosen.*
  * --flavor *-The server flavor type to use.*
  * --verbose *-Display the contents of the cloud-init and other extra info. **[OPTIONAL]**.*

#### RackConnect specific parameters
  * --rackconnect *-Add this option if RackConnect is in use, **[OPTIONAL]**.*
  * --load-balancer *-A RackConnect load balancer pool to use, **[OPTIONAL]**.*
  * --private-lan *-A private network to attach, **[OPTIONAL]**.*

#### Puppet and automation parameters
  * --ssh-authorized-keys *-Path of the ssh_authorized_keys to install.*
  * --puppet-host *-Hostname of the puppet master. Will be used to create a hosts entry in case DNS is unavailable.*
  * --puppet-ip *-IP address of the puppet master. Will be used to create a hosts entry in case DNS is unavailable.*
  * --nameservers *-A pair of nameservers to use, **[OPTIONAL]**.*

### Examples

#### Setup a Python virtual environment

	mkdir rackspace-puppet-bootstrap
	virtualenv rackspace-puppet-bootstrap
	cd rackspace-puppet-bootstrap
	git clone https://github.com/ordenull/rackspace-puppet-bootstrap.git rackspace-puppet-bootstrap
	source bin/activate
	cd rackspace-puppet-bootstrap
	./setup.py install

#### Execute the tool

	export RACKSPACE_USERNAME=change-me
	export RACKSPACE_APIKEY=1b2b3c4d5e111change-me111f1b2b3c4d5e6f
	../bin/rackspace-puppet-bootstrap test.xeraweb.net \
	--region ord \
	--rackconnect \
	--ssh-authorized-keys ~/.ssh/id_rsa.pub \
	--puppet-host puppet.xeraweb.net \
	--puppet-ip 10.123.123.123 \
	--flavor "general1-1" \
	--verbose

##Copyright and License

Copyright (C) 2016 [Stan Borbat](http://stan.borbat.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
