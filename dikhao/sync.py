# Utility to sync route53, ec2 details in redis.
# **** This must be the first import to be used in any module ****
#
# Author - @rohit01

import gevent
import gevent.monkey
gevent.monkey.patch_all()

import time
import dikhao.aws.ec2 as ec2
import dikhao.database.redis_handler

## Global variable for indexing
index_keys = []
INDEX = ['name', 'value', 'instance_id', 'private_ip_address', 'ip_address',
         'ec2_dns', 'ec2_private_dns', 'elb_name', 'elb_dns', 'elastic_ip',]


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
        region_list = ec2.get_region_list()
    else:
        region_list = [r.strip() for r in regions.split(',')]
    thread_list = []
    for region in region_list:
        ec2_handler = ec2.Ec2Handler(apikey, apisecret, region)
        thread = gevent.spawn(sync_ec2_instances, redis_handler, ec2_handler,
                              expire)
        thread_list.append(thread)
        thread = gevent.spawn(sync_ec2_elbs, redis_handler, ec2_handler,
                              expire)
        thread_list.append(thread)
        thread = gevent.spawn(sync_elastic_ips, redis_handler, ec2_handler,
                              expire)
        thread_list.append(thread)
    return thread_list

def sync_ec2_instances(redis_handler, ec2_handler, expire):
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

def sync_ec2_elbs(redis_handler, ec2_handler, expire):
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

def sync_elastic_ips(redis_handler, ec2_handler, expire):
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
    route53_handler = route53.Route53Handler(apikey=arguments['apikey'],
        apisecret=arguments['apisecret'])
    redis_handler = dikhao.database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'],
        password=arguments['redis_password'])
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
