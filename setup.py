#!/usr/bin/env python
#
# Python installation script
# Update pypi package after every update:
# $ python setup.py sdist bdist_wininst upload
# Author - @rohit01

import setuptools

requires = ['boto>=2.24.0', 'redis>=2.9.1', 'prettytable>=0.7.2',
            'gevent>=1.0', 'Flask==0.10.1', ]
VERSION = "0.0.6"

if __name__ == '__main__':
    setuptools.setup(
        name = "dikhao",
        py_modules = ["sync", "lookup"],
        version = VERSION,
        description = "Dikhao: A quick view of all related EC2 & Route53"
                      " resources",
        author = "Rohit Gupta",
        author_email = "hello@rohit.io",
        url = "https://github.com/rohit01/dikhao",
        keywords = ["dikhao", "ec2", "aws", "route53", "platform", "iaas"],
        install_requires = requires,
        classifiers = [
            "Programming Language :: Python",
            "Operating System :: OS Independent",
            "License :: OSI Approved :: MIT License",
            "Intended Audience :: Developers",
            "Development Status :: 4 - Beta",
            "Topic :: Utilities",
            "License :: OSI Approved :: MIT License"
        ],
        long_description = """
            Dikhao - A quick view of all related EC2 & Route53 resources.
            Main components:
            1. sync.py: It syncs all ec2 & route53 data into redis. Deploy this
                        as a cron job with high frequency
            2. lookup.py: Easy to use program to perform lookups on demand
        """ )
