#!/usr/bin/env python

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

requires = [
    'pyyaml',
    'apache-libcloud',
    ]

setup(name='rackspace-puppet-bootstrap',
      version='0.1',
      description='A tool to bootstrap RackSpace servers and connect them to RackConnect and Puppet',
      long_description=README,
      classifiers=[
        "Programming Language :: Python",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        ],
      author='Stan Borbat',
      author_email='stan@borbat.com',
      url='https://stan.borbat.com',
      keywords='rackspace rackconnect puppet bootstrap cloud init cloud-init puppetmaster',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points={
        'console_scripts': [
            'rackspace-puppet-bootstrap = rackspace_puppet_bootstrap.rackspace_puppet_bootstrap:main',
        ],
      },
)
