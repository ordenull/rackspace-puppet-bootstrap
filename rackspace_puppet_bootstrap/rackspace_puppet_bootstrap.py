#!/usr/bin/env python
'''
A tool to bootstrap RackSpace servers and connect them to RackConnect and Puppet.
Copyright (C) 2016 Stan Borbat <stan@borbat.com>

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
'''

import os
import sys
import argparse
from time import sleep
from yaml import safe_dump


USERNAME = os.getenv('RACKSPACE_USERNAME', None)
APIKEY = os.getenv('RACKSPACE_APIKEY', None)
HOSTS_TEMPLATE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ubuntu-hosts.tmpl'))

if USERNAME is None or APIKEY is None:
    print "The RACKSPACE_USERNAME and RACKSPACE_APIKEY need to be set"
    exit(1)

def main():
    """ This is the main entry point for the program """
    parser = argparse.ArgumentParser(description='A tool to bootstrap RackSpace servers and connect them to RackConnect and Puppet.')
    parser.add_argument('hostname', help='Fully qualified domain name of the new server')
    parser.add_argument('--region', type=str, nargs=1, metavar=('<ord|iad|dfw>'), help='RackSpace region to use')
    parser.add_argument('--image', type=str, nargs=1, metavar=('<uuid>'), help='The UUID of the image to use')
    parser.add_argument('--flavor', type=str, nargs=1, metavar=('<flavor>'), help='The server flavor type to use')
    parser.add_argument('--verbose', help='Display the contents of the cloud-init and other extra info', action="store_true")

    # RackConnect options
    parser.add_argument('--rackconnect', help='Add this option if RackConnect is in use', action="store_true")
    parser.add_argument('--load-balancer', type=str, nargs=1, metavar=('<pool>'), help='A RackConnect load balancer pool to use')
    parser.add_argument('--private-lan', type=str, nargs=1, metavar=('<uuid>'), help='A private network to attach')
    
    # Puppet automation options
    parser.add_argument('--ssh-authorized-keys', type=str, nargs=1, metavar=('<filename>'), help='Path of the ssh_authorized_keys to install')
    parser.add_argument('--puppet-host', type=str, nargs=1, metavar=('<hostname>'), help='Hostname of the puppet master')
    parser.add_argument('--puppet-ip', type=str, nargs=1, metavar=('<ip>'), help='IP address of the puppet master')
    parser.add_argument('--nameservers', type=str, nargs=2, metavar=('<nameserver>'), help='A pair of nameservers to use')

    args = parser.parse_args()
    
    config = dict()
    if args.ssh_authorized_keys is not None:
        with open(args.ssh_authorized_keys[0]) as f:
            config['ssh_keys'] = f.readlines()
        config['ssh_keys'] = [line.strip() for line in config['ssh_keys']]
    else:
        config['ssh_keys'] = None

    if args.region is not None:
        config['region'] = args.region[0]
    else:
        config['region'] = 'ord'

    parts = args.hostname.split('.')
    config['hostname'] = parts[0]
    config['domain'] = '.'.join(parts[1:])    
    config['rackconnect'] = args.rackconnect

    if args.puppet_host is not None:
        config['puppet_host'] = args.puppet_host[0]
    else:
        config['puppet_host'] = None

    config['nameservers'] = args.nameservers

    config['userdata'] = generate_cloud_init(
        config['hostname'],
        config['domain'],
        ssh_keys=config['ssh_keys'],
        nameservers=config['nameservers'],
        puppetmaster=config['puppet_host']
    )

    if args.puppet_ip is not None:
        with open (HOSTS_TEMPLATE, "r") as template:
            contents=template.read()
        contents += "\n" + args.puppet_ip[0] + " " + args.puppet_host[0] + "\n"
        config['personality'] = {
            '/etc/cloud/templates/hosts.debian.tmpl': contents
        }
    else:
        config['personality'] = {}

    config['metadata'] = dict()
    if args.load_balancer:
        config['metadata']['RackConnectLBPool'] = args.load_balancer[0].split(':')[0].strip()

    if args.private_lan:
        config['lan'] = args.private_lan[0].split(':')[0].strip()
    else:
        config['lan'] = None

    if args.image:
        config['image'] = args.image[0].split(':')[0].strip()
    else:
        config['image'] = None

    if args.flavor:
        config['flavor'] = args.flavor[0].split(':')[0].strip()
    else:
        config['flavor'] = None
    
    if args.verbose:
        print "============================ Generated user-data ============================="
        print config['userdata']
        print "=============================================================================="

    node_details = spawn_rackspace_host(config, verbose=args.verbose)
    
    print "{0} is running and ready".format(node_details.name)
    print "UUID: " + node_details.id
    print "Public IP: " + node_details.extra['access_ip']
    print "Private IPs: " + ' '.join(node_details.private_ips)

def generate_cloud_init(hostname, domain, ssh_keys=None, nameservers=None, puppetmaster=None):
    cloud_init = dict()

    cloud_init['hostname'] = hostname
    cloud_init['fqdn'] = '.'.join((hostname, domain))
    cloud_init['manage_etc_hosts'] = True
    cloud_init['disable_root'] = False
    cloud_init['ssh_pwauth'] = True
    cloud_init['resize_rootfs'] = True
    cloud_init['package_update'] = True

    if nameservers is not None:
        cloud_init['manage_resolv_conf'] = True
        cloud_init['resolv_conf'] = dict()
        cloud_init['resolv_conf']['nameservers'] = nameservers
        cloud_init['resolv_conf']['searchdomains'] = domain
        cloud_init['resolv_conf']['domain'] = domain
        cloud_init['resolv_conf']['options'] = {
            'rotate': True,
            'timeout': 1
        }

    if puppetmaster is not None:
        cloud_init['apt_sources'] = list()
        cloud_init['apt_sources'].append({
            'source': 'deb http://apt.puppetlabs.com $RELEASE main dependencies',
            'filename': 'puppetlabs.list',
            'keyid': '4BD6EC30'
        })
        cloud_init['puppet'] = { 'conf': { 'agent': { 'server': puppetmaster}}}
    
    if ssh_keys is not None:
        cloud_init['ssh_authorized_keys'] = ssh_keys
    
    cloud_init_text = safe_dump(cloud_init, default_flow_style=False)
    cloud_init_text = "#cloud-config\n\n" + cloud_init_text
    return cloud_init_text

def spawn_rackspace_host(config, verbose=False):
    import libcloud.security
    libcloud.security.VERIFY_SSL_CERT = True
    import libcloud.compute.providers
    import libcloud.compute.types

    Driver = libcloud.compute.providers.get_driver(libcloud.compute.types.Provider.RACKSPACE)
    driver = Driver(USERNAME, APIKEY, region=config['region'])

    if verbose:
        print("Querying RackSpace for available flavors")
    try:
        sizes = driver.list_sizes()
        if config['flavor'] is None:
            size_name = 'with 1GB of RAM'
            size = [s for s in sizes if s.ram == 1024][0]
        else:
            size_name = config['image']
            size = [s for s in sizes if s.id == config['flavor']][0]
    except IndexError as e:
        print("ERROR: Unable to find flavor {0}".format(size_name))
        exit(1)

    if verbose:
        print("Querying RackSpace for available images")
    images = driver.list_images()
    try:
        if config['image'] is None:
            image_name = 'Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)'
            image = [i for i in images if i.name == 'Ubuntu 14.04 LTS (Trusty Tahr) (PVHVM)'][0]
        else:
            image_name = 'with uuid=' + config['image']
            image = [i for i in images if i.id == config['image']][0]
    except IndexError as e:
        print("ERROR: Unable to find image {0}".format(image_name))
        exit(1)
        
    if verbose:
        print("Querying RackSpace for available networks")
    networks = driver.ex_list_networks()
    networks_to_use = list()
    for network in networks:
        if network.id == '11111111-1111-1111-1111-111111111111': # Private
            networks_to_use.append(network)
        if network.id == '00000000-0000-0000-0000-000000000000': # Public
            networks_to_use.append(network)
        if config['lan'] is not None and network.id == config['lan']:
            networks_to_use.append(network)

    if verbose:
        print("Instantiating a new server")
    node = driver.create_node(
        name=config['hostname'],
        image=image,
        size=size,
        ex_config_drive=True,
        ex_userdata=config['userdata'],
        ex_files=config['personality'],
        ex_metadata=config['metadata'],
        networks=networks_to_use
    )

    if verbose:
        print("Waiting for the new server to come online")
    driver._wait_until_running(node)

    if config['rackconnect']:
        if verbose:
            print("Waiting for RackConnect automation to complete")
        completed = False
        while not completed:
            try:
                metadata = driver.ex_get_metadata(node)
                if metadata.get('rackconnect_automation_status', "DEPLOYING") == "DEPLOYED":
                    completed = True
                if metadata.get('rackconnect_automation_status', "DEPLOYING") == "Failed":
                    completed = True
            except:
                pass
            sleep(5)

    if verbose:
        print("Getting the details of the new server")
    details = driver.ex_get_node_details(node)
    return details

if __name__ ==  "__main__":
    main()
