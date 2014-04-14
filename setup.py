#!/usr/bin/env python
#
# Python installation script
# Update pypi package after every update:
# $ python setup.py sdist bdist_wininst upload
# Author - @rohit01

import os.path
import setuptools
from dikhao import __version__


CLASSIFIERS = [
    "Programming Language :: Python",
    "Operating System :: OS Independent",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Developers",
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Topic :: Utilities",
    "License :: OSI Approved :: MIT License",
]

# read requirements
fname = os.path.join(os.path.dirname(__file__), 'requirements.txt')
with open(fname) as f:
    requires = list(map(lambda l: l.strip(), f.readlines()))

setuptools.setup(
    name = "dikhao",
    py_modules = ["padho", "batao", "dikhao.aws", "dikhao.aws.ec2",
                  "dikhao.aws.route53", "dikhao.database",
                  "dikhao.database.redis_handler", ],
    version = __version__,
    description = "Dikhao: A quick view of all related EC2 & Route53"
                  " resources",
    author = "Rohit Gupta",
    author_email = "hello@rohit.io",
    url = "https://github.com/rohit01/dikhao",
    keywords = ["dikhao", "ec2", "aws", "route53", "platform", "iaas"],
    install_requires = requires,
    packages=["dikhao", ],
    classifiers = CLASSIFIERS,
    entry_points="""
        [console_scripts]
        padho=padho:run
        batao=batao:run
    """,
    long_description = """
        Dikhao - A quick view of all related EC2 & Route53 resources.
        Main components:
        1. padho.py: It syncs all ec2 & route53 data into redis. Deploy this
                    as a cron job
        2. batao.py: Easy to use program to perform lookups on demand
    """,
)
