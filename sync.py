#!/usr/bin/env python
#
# Utility to sync route53, ec2 details in redis.
# This program should be deployed as a cron job with high frequency.
#
# Author - @rohit01

import optparse
import os

VERSION = """Version: 0.1,
Author: Rohit Gupta - @rohit01"""
DESCRIPTION = """Utility to sync route53, ec2 details in redis. The local 
redis cache helps in avoiding slow AWS API calls, thereby making the dns lookup
much faster. This program should be deployed as a cron job with high frequency.
"""
OPTIONS = {
    'a': "apikey;AWS Credential - API key",
    's': "apisecret;AWS Credential - API Secret key",
    'r': "regions;AWS region api names separated by comma. Applicable only if"
         " -e option is used. Default: All",
    'e': "expire-duration;Duration (in seconds) for which, dns entries are"
         " stored in redis. Pass 0 for infinity. Default: 24 hours",
    'H': "redis-host;Address of redis server. Default: localhost",
    'p': "redis-port-no;Port No. of redis server. Default: 6379",
}
FLAG_OPTIONS = {
    'E': "no-ec2;Dont sync ec2 instance details in redis. Private ip and "
         "ec2 dns mapping with Route53 will be disabled",
    'R': "no-route53;Dont sync route53 details in redis. If route53 sync is"
         " disabled, only ec2 dns details will be available",
    't': "ttl;Use DNS ttl value as expiry of local DNS entries in Redis",
}
USAGE = "%s -a <aws api key> -s <aws secret key> [-r <aws regions>]" \
        " [-e <no of seconds>] [-H <redis host address>] [-p <port no>] [-E]" \
        " [-R] [-t] [-v]" % os.path.basename(__file__)


def parse_options():
    parser = optparse.OptionParser(description=DESCRIPTION, usage=USAGE, 
                                   version=VERSION)
    for option, description in OPTIONS.items():
        shortopt = '-%s' % (option)
        longopt = '--%s' % (description.split(';')[0])
        keyname = description.split(';')[0]
        help = ''
        if len(description.split(';')) > 1:
            help = description.split(';')[1]
        parser.add_option(shortopt, longopt, dest=keyname, help=help)
    for option, description in FLAG_OPTIONS.items():
        shortopt = '-%s' % (option)
        longopt = '--%s' % (description.split(';')[0])
        keyname = description.split(';')[0]
        help = ''
        if len(description.split(';')) > 1:
            help = description.split(';')[1]
        parser.add_option(shortopt, longopt, dest=keyname,
                          action="store_true", help=help)
    (options, args) = parser.parse_args()
    return options


arguments = parse_options()
print arguments

