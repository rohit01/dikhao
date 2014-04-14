#!/usr/bin/env python
#
# Program to sync route53, ec2 details in redis.
# This program should be deployed as a cron job to regularly perform lookups
# using CLI tool: batao.py
#
# Author - @rohit01

import os
import sys
import gevent
import dikhao.util
import dikhao.sync
import dikhao.aws.route53
from dikhao import __version__


VERSION = """Version: %s, Author: Rohit Gupta - @rohit01""" % __version__
DESCRIPTION = """Utility to sync route53, ec2 details in redis. The local
redis cache helps in avoiding slow AWS API calls, thereby making the dns lookup
much faster. This program should be deployed as a cron job.
"""
OPTIONS = {
    'a': "apikey;AWS Credential - API key",
    's': "apisecret;AWS Credential - API Secret key",
    'r': "regions;AWS region api names separated by comma. Applicable only if"
         " -e option is used. Default: All",
    'z': "hosted_zones;Route53 Hosted zone names separated by comma."
         " Default: All",
    'e': "expire_duration;Duration (in seconds) for which, dns entries are"
         " stored in redis. Pass 0 for infinity. Default: 86400 (1 Day)",
    'H': "redis_host;Address of redis server. Default: localhost",
    'P': "redis_port_no;Port No. of redis server. Default: 6379",
    'p': "redis_password;Redis password (optional)",
}
FLAG_OPTIONS = {
    'E': "no_ec2;Dont sync ec2 instance details in redis. Private ip and "
         "ec2 dns mapping with Route53 will be disabled",
    'R': "no_route53;Dont sync route53 details in redis. If route53 sync is"
         " disabled, only ec2 dns details will be available",
    't': "ttl;Use DNS ttl value as expire for Route53 cache in Redis. WARNING"
         " - Use with caution: If ttl values are very low, it may lead to a"
         " highly volatile cache",
}
USAGE = "%s -a <aws api key> -s <aws secret key> [-r <aws regions>]" \
        " [-e <no of seconds>] [-H <redis host address>] [-p <port no>] [-E]" \
        " [-R] [-t] [--version]" % os.path.basename(__file__)
DEFAULTS = {
    "regions": "all",
    "hosted_zones": "all",
    "expire_duration": 86400,
    "redis_host": "127.0.0.1",
    "redis_port_no": 6379,
    "no_ec2": False,
    "no_route53": False,
    "ttl": False,
    "redis_password": '',
}


def validate_arguments(option_args):
    apikey = option_args.apikey or DEFAULTS.get('apikey', None)
    apisecret = option_args.apisecret or DEFAULTS.get('apisecret', None)
    regions = option_args.regions or DEFAULTS.get('regions', None)
    hosted_zones = option_args.hosted_zones or DEFAULTS.get('hosted_zones',
                                                            None)
    expire_duration = option_args.expire_duration or DEFAULTS.get(
        'expire_duration', None)
    redis_host = option_args.redis_host or DEFAULTS.get('redis_host', None)
    redis_port_no = option_args.redis_port_no or DEFAULTS.get('redis_port_no',
                                                              None)
    redis_password = option_args.redis_password or DEFAULTS.get(
        'redis_password', None)
    no_ec2 = option_args.no_ec2 or DEFAULTS.get('no_ec2', None)
    no_route53 = option_args.no_route53 or DEFAULTS.get('no_route53', None)
    ttl = option_args.ttl or DEFAULTS.get('ttl', None)
    arguments = {
        "apikey": apikey,
        "apisecret": apisecret,
        "regions": regions,
        "hosted_zones": hosted_zones,
        "expire_duration": expire_duration,
        "redis_host": redis_host,
        "redis_port_no": redis_port_no,
        "redis_password": redis_password,
        "no_ec2": no_ec2,
        "no_route53": no_route53,
        "ttl": ttl,
    }
    mandatory_missing = []
    for k, v in arguments.items():
        if v is None:
            mandatory_missing.append(k)
    if len(mandatory_missing) > 0:
        print "Mandatory arguments missing: --%s\nUse: -h/--help for details" \
              % ', --'.join(mandatory_missing)
        sys.exit(1)
    try:
        arguments["expire_duration"] = int(arguments["expire_duration"])
    except ValueError as e:
        print "Invalid value passed for option --expire_duration (%s). It" \
              " should be a valid Integer" % arguments["expire_duration"]
        sys.exit(1)
    try:
        arguments["redis_port_no"] = int(arguments["redis_port_no"])
    except ValueError as e:
        print "Invalid value passed for option --redis_port_no (%s). It" \
              " should be a valid Integer" % arguments["redis_port_no"]
        sys.exit(1)
    if (option_args.expire_duration is not None) and option_args.ttl:
        print "Only one of the option between --expire_duration and --ttl," \
              " can be used. Please use -h/--help for details."
        sys.exit(1)
    if arguments["no_ec2"] and arguments["no_route53"]:
        print "Only one of the option between --no_ec2 and --no_route53," \
              " can be used. Please use -h/--help for details."
        sys.exit(1)
    return arguments


def run():
    option_args = dikhao.util.parse_options(options=OPTIONS,
        flag_options=FLAG_OPTIONS, description=DESCRIPTION, usage=USAGE,
        version=VERSION)
    arguments = validate_arguments(option_args)
    route53_handler = dikhao.aws.route53.Route53Handler(
        apikey=arguments['apikey'],
        apisecret=arguments['apisecret']
    )
    redis_handler = dikhao.database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'],
        password=arguments['redis_password'])
    thread_list = []
    if not arguments['no_route53']:
        new_threads = dikhao.sync.sync_route53(route53_handler, redis_handler,
            arguments['hosted_zones'], expire=arguments['expire_duration'],
            ttl=arguments['ttl'])
        thread_list.extend(new_threads)
    if not arguments['no_ec2']:
        new_threads = dikhao.sync.sync_ec2(
            redis_handler,
            apikey=arguments["apikey"],
            apisecret=arguments["apisecret"],
            regions=arguments['regions'],
            expire=arguments['expire_duration']
        )
        thread_list.extend(new_threads)
    print 'Sync Started... . . .  .  .   .     .     .'
    gevent.joinall(thread_list)
    print 'Cleanup stale records initiated...'
    dikhao.sync.clean_stale_entries(redis_handler,
                                    clean_route53=not arguments['no_route53'],
                                    clean_ec2=not arguments['no_ec2'])
    print 'Details saved. Indexing records!'
    dikhao.sync.index_records(redis_handler,
                              expire=arguments['expire_duration'])
    print 'Complete'


if __name__ == '__main__':
    run()