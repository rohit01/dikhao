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
from setup import VERSION

VERSION = """Version: %s,
Author: Rohit Gupta - @rohit01""" % VERSION
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
    "ec2_private_dns": "Private DNS",
    "region": "Region",
    "instance_id": "Instance ID",
    "ec2_dns": "EC2 DNS",
    "state": "State",
    "private_ip_address": "Private IP address",
    "ip_address": "IP address",
    "instance_elb_names": "ELB names",
}
EC2_ITEM_ORDER = [
    "instance_id",
    "state",
    "ec2_dns",
    "ip_address",
    "region",
    "zone",
    "instance_type",
    "private_ip_address",
    "ec2_private_dns",
    "instance_elb_names",
]
OUTPUT_ORDER = [
    'route53',
    'ec2',
    'elastic_ip',
    'elb',
]
LOOKUP_INDEX = sync.INDEX + ['instance_elb_names']


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

def get_index(redis_handler, host):
    fqdn, pqdn = util.generate_fqdn_and_pqdn(host)
    ## Get Index
    fqdn_index = redis_handler.get_index(fqdn) or ''
    pqdn_index = redis_handler.get_index(pqdn) or ''
    ## Merge indexes
    index_value = ','.join([i for i in (fqdn_index, pqdn_index) if i])
    ## Remove duplicates
    index_value = ','.join(set(index_value.split(',')))
    return index_value

def search(redis_handler, host):
    index_value = get_index(redis_handler, host)
    if not index_value:
        return None
    ## Initial search
    match_found = {}
    for hash_key in index_value.split(','):
        if not hash_key.strip():
            continue
        details = redis_handler.get_details(hash_key)
        if not details:
            continue
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
        ## Check for clues in initial search results
        details = match_found[hash_key][0]
        ## Search indexed items
        for key, comma_sep_values in details.items():
            for value in comma_sep_values.split(','):
                if key not in LOOKUP_INDEX:
                    continue
                if not value:
                    continue
                if redis_handler.get_index_hash_key(value) in match_found:
                    continue
                index_value = get_index(redis_handler, value)
                if index_value is None:
                    continue
                for new_hash_key in index_value.split(','):
                    if new_hash_key in match_found:
                        continue
                    details = redis_handler.get_details(new_hash_key)
                    if not details:
                        continue
                    match_found[new_hash_key] = [details, False]
    categorize_match = {
        'route53': [],
        'instance': [],
        'elb': [],
        'elastic_ip': [],
    }
    for k, v in match_found.items():
        if k.startswith(redis_handler.route53_hash_prefix):
            categorize_match['route53'].append(v[0])
        elif k.startswith(redis_handler.instance_hash_prefix):
            categorize_match['instance'].append(v[0])
        elif k.startswith(redis_handler.elb_hash_prefix):
            categorize_match['elb'].append(v[0])
        elif k.startswith(redis_handler.elastic_ip_hash_prefix):
            categorize_match['elastic_ip'].append(v[0])
    return categorize_match

def formatted_output(redis_handler, match_dict):
    formatted_dict = {}
    time_now = int(time.time())
    if match_dict.get('route53', None) and len(match_dict['route53']):
        last_updated = 0
        cli_table = prettytable.PrettyTable(["Name", "ttl", "Type", "Value"])
        cli_table.align = 'l'
        for details in match_dict['route53']:
            row = [
                details['name'], details['ttl'], details['type'],
                '\n'.join(details['value'].split(','))
            ]
            cli_table.add_row(row)
            if int(details.get('timestamp', 0)) > last_updated:
                last_updated = int(details.pop('timestamp'))
        formatted_dict['route53'] = {}
        formatted_dict['route53']['header'] = "Route53 Details (%s secs ago):" \
                                    % (time_now - last_updated)
        formatted_dict['route53']['content'] = [cli_table.get_string()]
    if match_dict.get('instance', None) and len(match_dict['instance']):
        last_updated = 0
        formatted_dict['ec2'] = {}
        formatted_dict['ec2']['content'] = []
        for details in match_dict['instance']:
            cli_table = prettytable.PrettyTable(["Property", "Value"])
            cli_table.align["Property"] = 'r'
            cli_table.align["Value"] = 'l'
            if int(details.get('timestamp', 0)) > last_updated:
                last_updated = int(details.pop('timestamp'))
            ## Display items in order
            for k in EC2_ITEM_ORDER:
                v = details.pop(k, None)
                if v:
                    k = FORMAT_EC2.get(k, k)
                    cli_table.add_row([k, v])
            ## Display remaining items
            for k, v in details.items():
                k = FORMAT_EC2.get(k, k)
                cli_table.add_row([k, v])
            formatted_dict['ec2']['content'].append(cli_table.get_string())
        formatted_dict['ec2']['header'] = "EC2 Instance Details (%s secs" \
                                          " ago):" % (time_now - last_updated)
    if match_dict.get('elastic_ip', None) and len(match_dict['elastic_ip']):
        last_updated = 0
        cli_table = prettytable.PrettyTable(["Elastic IP", "Instance ID"])
        for details in match_dict['elastic_ip']:
            row = [details['elastic_ip'], details['instance_id'], ]
            cli_table.add_row(row)
            if int(details.get('timestamp', 0)) > last_updated:
                last_updated = int(details.pop('timestamp'))
        formatted_dict['elastic_ip'] = {}
        formatted_dict['elastic_ip']['header'] = "Elastic IP Details (%s" \
            " secs ago):" % (time_now - last_updated)
        formatted_dict['elastic_ip']['content'] = [cli_table.get_string()]
    if match_dict.get('elb', None) and len(match_dict['elb']):
        last_updated = 0
        cli_table = prettytable.PrettyTable(["Name", "ELB DNS", "Instance ID",
            "State"])
        cli_table.align = 'l'
        for details in match_dict['elb']:
            instance_id_list = []
            instance_state_list = []
            instances = details['elb_instances']
            for i in instances.split(','):
                instance_id, state = i.split(' ')
                instance_id_list.append(instance_id)
                instance_state_list.append(state)
            cli_table.add_row([details['elb_name'], details['elb_dns'],
                '\n'.join(instance_id_list), '\n'.join(instance_state_list),
            ])
            if int(details.get('timestamp', 0)) > last_updated:
                last_updated = int(details.pop('timestamp'))
        formatted_dict['elb'] = {}
        formatted_dict['elb']['header'] = "ELB Details (%s secs ago):" \
                                          % (time_now - last_updated)
        formatted_dict['elb']['content'] = [cli_table.get_string()]
    return formatted_dict

def string_details(details):
    output_list = []
    for item in OUTPUT_ORDER:
        if details.get(item, None):
            output_list.append(details[item]['header'])
            for content in details[item]['content']:
                output_list.append(content)
            details.pop(item, None)
    return '\n'.join(output_list)


if __name__ == '__main__':
    option_args = util.parse_options(options=OPTIONS, description=DESCRIPTION,
        usage=USAGE, version=VERSION)
    arguments = validate_arguments(option_args)
    redis_handler = database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'])
    match_dict = search(redis_handler, host=arguments['input_lookup'])
    if match_dict:
        details = formatted_output(redis_handler, match_dict)
        print string_details(details)
    else:
        print 'Sorry! No entry found'
        sys.exit(1)
