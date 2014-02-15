#!/usr/bin/env python
#
# Utility to sync route53, ec2 details in redis.
# This program should be deployed as a cron job with high frequency.
#
# Author - @rohit01

import gevent
import gevent.monkey
gevent.monkey.patch_all()

import os
import sys
import time
import util
import aws.ec2
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
}

## Global variable for indexing
index_keys = []
INDEX = ['name', 'value', 'instance_id', 'private_ip_address', 'ip_address',
         'ec2_dns', 'ec2_private_dns', 'elb_name', 'elb_dns', 'elastic_ip',]


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

def sync_route53(route53_handler, redis_handler, hosted_zones, expire, ttl):
    global index_keys
    try:
        route53_zone_details = route53_handler.fetch_route53_zone_details(
            hosted_zones)
    except Exception as e:
        print "Exception while fetching route53 hosted zones, message: %s" \
              % e.message
        return
    thread_list = []
    for zone_name, zone_id in route53_zone_details.items():
        thread = gevent.spawn(sync_route53_zone, route53_handler,
            redis_handler, zone_name, zone_id, expire, ttl)
        thread_list.append(thread)
    return thread_list

def sync_route53_zone(route53_handler, redis_handler, zone_name, zone_id,
                      expire, ttl):
    try:
        record_sets = route53_handler.fetch_all_route53dns_rsets(zone_id)
    except Exception as e:
        print "Exception for Route53 Zone: %s, message: %s" % (zone_name,
                                                               e.message)
        return
    for record in record_sets:
        item_details = {}
        item_details['name'] = record.name
        item_details['ttl'] = record.ttl
        item_details['type'] = record.type
        item_details['value'] = record.to_print()
        item_details['timestamp'] = int(time.time())
        if record.alias_dns_name is not None:
            item_details['type'] = '%s (Alias)' % record.type
            item_details['value'] = record.alias_dns_name
        hash_key, status = redis_handler.save_route53_details(item_details)
        index_keys.append(hash_key)
        if ttl:
            try:
                redis_handler.expire(hash_key, int(item_details['ttl']))
            except ValueError:
                redis_handler.expire(hash_key, expire)
        elif expire > 0:
            redis_handler.expire(hash_key, expire)
    print "Sync complete for Route53 zone: %s" % zone_name

def sync_ec2(redis_handler, apikey, apisecret, regions, expire):
    if (regions is None) or (regions == 'all'):
        region_list = aws.ec2.get_region_list()
    else:
        region_list = [r.strip() for r in regions.split(',')]
    thread_list = []
    for region in region_list:
        ec2_handler = aws.ec2.Ec2Handler(apikey, apisecret, region)
        thread = gevent.spawn(sync_ec2_instances, ec2_handler, expire)
        thread_list.append(thread)
        thread = gevent.spawn(sync_ec2_elbs, ec2_handler, expire)
        thread_list.append(thread)
        thread = gevent.spawn(sync_elastic_ips, ec2_handler, expire)
        thread_list.append(thread)
    return thread_list

def sync_ec2_instances(ec2_handler, expire):
    global index_keys
    try:
        instance_list = ec2_handler.fetch_all_instances()
    except Exception as e:
        print "Exception for EC2 in Region: %s, message: %s" \
              % (ec2_handler.region, e.message)
        return
    for instance in instance_list:
        instance_details = ec2_handler.get_instance_details(instance)
        instance_details['timestamp'] = int(time.time())
        hash_key, status = redis_handler.save_instance_details(instance_details)
        index_keys.append(hash_key)
        if expire > 0:
            redis_handler.expire(hash_key, expire)
    print "Instance sync complete for ec2 region: %s" % ec2_handler.region

def sync_ec2_elbs(ec2_handler, expire):
    global index_keys
    try:
        elb_list = ec2_handler.fetch_all_elbs()
    except Exception as e:
        print "Exception for ELB in Region: %s, message: %s" \
              % (ec2_handler.region, e.message)
        return
    for elb in elb_list:
        details, instance_id_list = ec2_handler.get_elb_details(elb)
        details['timestamp'] = int(time.time())
        for instance_id in instance_id_list:
            instance_elb_names = redis_handler.get_instance_item_value(
                region=details['region'], instance_id=instance_id,
                key='instance_elb_names'
            ) or ''
            instance_elb_names = set(instance_elb_names.split(','))
            if '' in instance_elb_names:
                instance_elb_names.remove('')
            instance_elb_names.add(elb.name)
            instance_elb_names = ','.join(instance_elb_names)
            redis_handler.add_instance_details(
                region=details['region'], instance_id=instance_id,
                key='instance_elb_names', value=instance_elb_names,
            )
        hash_key, status = redis_handler.save_elb_details(details)
        index_keys.append(hash_key)
        if expire > 0:
            redis_handler.expire(hash_key, expire)
    print "ELB sync complete for ec2 region: %s" % ec2_handler.region

def sync_elastic_ips(ec2_handler, expire):
    global index_keys
    try:
        elastic_ip_list = ec2_handler.fetch_elastic_ips()
    except Exception as e:
        print "Exception for Elastic IPs in Region: %s, message: %s" \
              % (ec2_handler.region, e.message)
        return
    for elastic_ip in elastic_ip_list:
        details = ec2_handler.get_elastic_ip_detail(elastic_ip)
        details['timestamp'] = int(time.time())
        hash_key, status = redis_handler.save_elastic_ip_details(details)
        index_keys.append(hash_key)
        if expire > 0:
            redis_handler.expire(hash_key, expire)
    print "Elastic ip sync complete for ec2 region: %s" % ec2_handler.region

def index_records(redis_handler, expire):
    global index_keys
    for hash_key in index_keys:
        details = redis_handler.get_details(hash_key)
        for key, value in details.items():
            if key not in INDEX:
                continue
            ## SRV records may contain ','. We need to separate values for
            ## effective indexing
            for v in value.split(','):
                v = v.split(' ')[-1]
                save_index(redis_handler, hash_key, v)
                redis_handler.expire_index(v, expire)

def save_index(redis_handler, hash_key, value):
    index_value = redis_handler.get_index(value)
    if index_value:
        index_value = "%s,%s" % (index_value, hash_key)
    else:
        index_value = hash_key
    ## Remove redundant values
    indexed_keys = set(index_value.split(','))
    ## Clean stale entries
    for k in indexed_keys.copy():
        if not redis_handler.exists(k):
            indexed_keys.remove(k)
    ## Save Index
    if len(indexed_keys) > 0:
        redis_handler.save_index(value, ','.join(indexed_keys))
    else:
        redis_handler.delete_index(value)

def clean_stale_entries(redis_handler, clean_route53=True, clean_ec2=True):
    if clean_route53:
        redis_handler.clean_route53_entries(valid_keys=index_keys)
    if clean_ec2:
        redis_handler.clean_instance_entries(valid_keys=index_keys)
        redis_handler.clean_elb_entries(valid_keys=index_keys)
        redis_handler.clean_elastic_ip_entries(valid_keys=index_keys)


if __name__ == '__main__':
    option_args = util.parse_options(options=OPTIONS,
        flag_options=FLAG_OPTIONS, description=DESCRIPTION, usage=USAGE,
        version=VERSION)
    arguments = validate_arguments(option_args)
    route53_handler = aws.route53.Route53Handler(apikey=arguments['apikey'],
        apisecret=arguments['apisecret'])
    redis_handler = database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'])

    thread_list = []
    if not arguments['no_route53']:
        new_threads = sync_route53(route53_handler, redis_handler,
            arguments['hosted_zones'], expire=arguments['expire_duration'],
            ttl=arguments['ttl'])
        thread_list.extend(new_threads)
    if not arguments['no_ec2']:
        new_threads = sync_ec2(redis_handler, apikey=arguments["apikey"],
                 apisecret=arguments["apisecret"],
                 regions=arguments['regions'],
                 expire=arguments['expire_duration'])
        thread_list.extend(new_threads)
    print 'Sync Started... . . .  .  .   .     .     .'
    gevent.joinall(thread_list)
    print 'Cleanup stale records initiated...'
    clean_stale_entries(redis_handler,
                        clean_route53=not arguments['no_route53'],
                        clean_ec2=not arguments['no_ec2'])
    print 'Details saved. Indexing records!'
    index_records(redis_handler, expire=arguments['expire_duration'])
    print 'Complete'
