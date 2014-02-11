#!/usr/bin/env python
#
# Program to perform dns and reverse dns lookup from locally synced redis DB.
#
# Author - @rohit01

import os
import sys
import time
import prettytable
import util
import sync
import database.redis_handler

VERSION = """Version: 0.1,
Author: Rohit Gupta - @rohit01"""
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
FORMAT_EC2 = {
    "zone": "Zone",
    "instance_type": "Instance type",
    "ec2_private_dns": "Private dns",
    "region": "Region",
    "instance_id": "Instance id",
    "ec2_dns": "EC2 dns",
    "state": "State",
    "private_ip_address": "Private IP address",
    "ip_address": "IP address",
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


def lookup(redis_handler, host):
    ## Get Index
    index_value = redis_handler.get_index(host)
    if not index_value:
        return None
    ## Initial search
    match_found = {}
    for hash_key in index_value.split(','):
        details = redis_handler.get_details(hash_key)
        match_found[hash_key] = [details, False]  ## False to indicate
                                                  ## further search can be done
    ## Full search
    while True:
        match_keys = [ key for key in match_found.keys()
                       if match_found[key][1] == False ]
        if len(match_keys) == 0:
            break
        hash_key = match_keys.pop()
        match_found[hash_key][1] = True

        details = match_found[hash_key][0]
        for key, value in details.items():
            if key not in sync.INDEX:
                continue
            if redis_handler.get_index_hash_key(value) in match_found:
                continue
            index_value = redis_handler.get_index(value)
            if index_value is None:
                continue
            for new_hash_key in index_value.split(','):
                if new_hash_key in match_found:
                    continue
                details = redis_handler.get_details(new_hash_key)
                match_found[new_hash_key] = [details, False]  ## False to
                                        ## indicate further search can be done
    for k, v in match_found.items():
        match_found[k] = v[0]
    return match_found

def formatted_output(redis_handler, match_dict):
    route53_table = prettytable.PrettyTable(["Name", "ttl", "Type", "Value"])
    route53_table.align = 'l'
    ec2_table = prettytable.PrettyTable(["Property", "Value"])
    ec2_table.align = 'l'
    last_updated = 0
    for hash_key, details in match_dict.items():
        if hash_key.startswith(redis_handler.route53_hash_prefix):
            row = [
                details['name'], details['ttl'], details['type'],
                '\n'.join(details['value'].split(','))
            ]
            route53_table.add_row(row)
            if int(details['timestamp']) > last_updated:
                last_updated = int(details['timestamp'])
        elif hash_key.startswith(redis_handler.ec2_hash_prefix):
            if int(details['timestamp']) > last_updated:
                last_updated = int(details['timestamp'])
            for k, v in details.items():
                if k == 'timestamp':
                    continue
                k = FORMAT_EC2[k] or k
                ec2_table.add_row([k, v])
    print "Route53 Details:"
    print route53_table
    print "EC2 Instance Details:"
    print ec2_table
    delay = int(time.time()) - last_updated
    print "Last updated: %s %s ago" % (delay, 'seconds')


if __name__ == '__main__':
    option_args = util.parse_options(options=OPTIONS, description=DESCRIPTION,
        usage=USAGE, version=VERSION)
    arguments = validate_arguments(option_args)
    redis_handler = database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'])
    match_dict = lookup(redis_handler, host=arguments['input_lookup'])
    if match_dict:
        formatted_output(redis_handler, match_dict)
    else:
        print 'Sorry! No entry found'
        sys.exit(1)
