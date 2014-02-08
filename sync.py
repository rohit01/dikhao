#!/usr/bin/env python
#
# Utility to sync route53, ec2 details in redis.
# This program should be deployed as a cron job with high frequency.
#
# Author - @rohit01

import optparse
import util
import sys
import os
import aws.route53
import database.redis_handler

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
    'z': "hosted_zones;Route53 Hosted zone names separated by comma."
         " Default: All",
    'e': "expire_duration;Duration (in seconds) for which, dns entries are"
         " stored in redis. Pass 0 for infinity. Default: 86400 (1 Day)",
    'H': "redis_host;Address of redis server. Default: localhost",
    'p': "redis_port_no;Port No. of redis server. Default: 6379",
}
FLAG_OPTIONS = {
    'E': "no_ec2;Dont sync ec2 instance details in redis. Private ip and "
         "ec2 dns mapping with Route53 will be disabled",
    'R': "no_route53;Dont sync route53 details in redis. If route53 sync is"
         " disabled, only ec2 dns details will be available",
    't': "ttl;Use DNS ttl value as expiry of local DNS entries in Redis",
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
    arguments["expire_duration"] = int(arguments["expire_duration"])
    arguments["redis_port_no"] = int(arguments["redis_port_no"])
    return arguments


def sync_route53(route53_handler, redis_handler, hosted_zones):
    route53_zone_details = route53_handler.fetch_route53_zone_details(
        hosted_zones)
    for zone_name, zone_id in route53_zone_details.items():
        record_sets = route53_handler.fetch_all_route53dns_rsets(zone_id)
        for record in record_sets:
            item_details = {}
            item_details['ttl'] = record.ttl
            item_details['type'] = record.type
            item_details['name'] = record.name
            item_details['value'] = record.to_print()
            item_details['zone_name'] = zone_name
            if record.type == 'A' and record.alias_dns_name is not None:
                item_details['alias'] = True
                item_details['value'] = record.alias_dns_name
            else:
                item_details['alias'] = False
            redis_handler.save_dns_record(zone_name, item_details)


if __name__ == '__main__':
    option_args = util.parse_options(options=OPTIONS, flag_options=FLAG_OPTIONS,
                                   description=DESCRIPTION, usage=USAGE,
                                   version=VERSION)
    arguments = validate_arguments(option_args)
    route53_handler = aws.route53.Route53Handler(apikey=arguments['apikey'],
        apisecret=arguments['apisecret'])
    redis_handler = database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'],
        expire=arguments['expire_duration'])
    sync_route53(route53_handler, redis_handler, arguments['hosted_zones'])
