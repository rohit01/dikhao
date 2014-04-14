#!/usr/bin/env python
#
# Search input in locally synced redis DB.
#
# Author - @rohit01

import os
import sys
import dikhao.util
import dikhao.search
from dikhao import __version__


VERSION = """Version: %s, Author: Rohit Gupta - @rohit01""" % __version__
DESCRIPTION = """Program to perform dns and reverse dns lookup from locally
synced redis DB.
"""
OPTIONS = {
    'i': "input_lookup;Input for lookup. Valid values: IP address or domain"
         " name",
    'H': "redis_host;Address of redis server. Default: localhost",
    'p': "redis_port_no;Port No. of redis server. Default: 6379",
}
USAGE = "%s -i <IP/DNS> -a <aws api key> -s <aws secret key>" \
    " [-H <redis host address>] [-p <port no>]"  % os.path.basename(__file__)
DEFAULTS = {
    "redis_host": "127.0.0.1",
    "redis_port_no": 6379,
}


def validate_arguments(option_args):
    input_lookup = option_args.input_lookup or DEFAULTS.get('input_lookup', None)
    redis_host = option_args.redis_host or DEFAULTS.get('redis_host', None)
    redis_port_no = option_args.redis_port_no or DEFAULTS.get('redis_port_no', None)
    arguments = {
        "input_lookup": input_lookup,
        "redis_host": redis_host,
        "redis_port_no": redis_port_no,
    }
    mandatory_missing = []
    for k, v in arguments.items():
        if v is None:
            mandatory_missing.append(k)
    if len(mandatory_missing) > 0:
        print "Mandatory arguments missing: --%s\nUse: -h/--help for details" \
              % ', --'.join(mandatory_missing)
        sys.exit(1)
    return arguments


def run():
    option_args = dikhao.util.parse_options(options=OPTIONS,
        description=DESCRIPTION, usage=USAGE, version=VERSION)
    arguments = validate_arguments(option_args)
    redis_handler = dikhao.database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'])
    match_dict = dikhao.search.search(redis_handler,
                                      host=arguments['input_lookup'])
    if match_dict:
        details = dikhao.search.formatted_output(redis_handler, match_dict)
        print dikhao.search.string_details(details)
    else:
        print 'Sorry! No entry found'
        sys.exit(1)


if __name__ == '__main__':
    run()
