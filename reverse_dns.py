## Need Route53 Access, EC2 Access, Structure code, CLI parameters, Description
## 


import redis
import time
import socket
import boto
import boto.ec2
from boto.route53.connection import Route53Connection
import optparse

## Redis DB details
REDIS_SERVER = '127.0.0.1'
REDIS_PORT = 6379
## AWS Credentials
AWS_ACCESS_KEY_ID = '<API Key>'
AWS_SECRET_ACCESS_KEY = '<API Secret>'
REGION_LIST = ['us-west-1', 'us-east-1', 'eu-west-1', 'ap-southeast-1',
               'us-west-2', 'ap-southeast-2', 'ap-northeast-1', 'sa-east-1']
## Redis key prefix -- 'AWS:Route53:<zone_name>:<ip/DNS>:<dns_name>:<type>'
HASH_PREFIX = 'AWS:Route53:%s:%s:%s:%s'
EXPIRE_DURATION = 43200
TRACK_SAVED_ITEMS = {}

redis_conn = redis.StrictRedis(REDIS_SERVER, REDIS_PORT)
route53_conn = Route53Connection(aws_access_key_id=AWS_ACCESS_KEY_ID,
                                 aws_secret_access_key=AWS_SECRET_ACCESS_KEY)


OPTIONS = {
    'H': 'hostname;DNS/IP address of server',
    's': 'sync;Dump DNS details in redis',
}


def parse_options(options):
    parser = optparse.OptionParser()
    for o in options:
        option = o.split(';')[0]
        shortopt = '-%s' % (option)
        longopt = '--%s' % (options[option].split(';')[0])
        keyname = options[option].split(';')[0]
        help = ''
        if len(o.split(';')) > 1:
            help = o.split(';')[1]
        elif len(options[option].split(';')) > 1:
            help = options[option].split(';')[1]
        parser.add_option(shortopt, longopt, dest=keyname, help=help)
    (arguments_passed, args) = parser.parse_args()
    return arguments_passed


def get_details(hash_key):
    return redis_conn.hgetall(hash_key)


def resolve_dns_to_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


def fetch_all_route53dns_rsets(zone_id):
    record_sets = route53_conn.get_all_rrsets(zone_id)
    rsets = record_sets
    while rsets.is_truncated is True:
        next_record_name = rsets.next_record_name
        next_record_type = rsets.next_record_type
        rsets = route53_conn.get_all_rrsets(zone_id, name=next_record_name,
                                           type=next_record_type)
        record_sets.extend(rsets)
    return record_sets


def fetch_hosted_zone_details():
    hosted_zone_details = {}
    hosted_zones = route53_conn.get_all_hosted_zones()
    for zone in hosted_zones['ListHostedZonesResponse']['HostedZones']:
        zone_id = zone['Id'].split('/')[-1]
        zone_name = zone['Name']
        hosted_zone_details[zone_name] = zone_id
    return hosted_zone_details


def save_dns_record(zone_name, item_details):
    key_list = []
    name = item_details['name']
    value = item_details['value']
    dns_type = item_details['type']
    alias = item_details['alias']
    item_details.pop('alias')
    if dns_type == 'A':
        key_list = [name, value]
        if alias is True:
            ip_address = resolve_dns_to_ip(value)
            if ip_address is not None:
                key_list.append(ip_address)
    elif dns_type == 'SRV':
        key_list = [name]
        for v in value.split(','):
            v = v.split(' ')[-1]
            key_list.append(v)
            ip_address = resolve_dns_to_ip(v)
            if ip_address is not None:
                key_list.append(ip_address)
    elif dns_type == 'CNAME':
        key_list = [name, value]
        ip_address = resolve_dns_to_ip(value)
        if ip_address is not None:
            key_list.append(ip_address)
    else:
        return
    for key in key_list:
        save_hash_key = HASH_PREFIX % (zone_name, key, name, dns_type)
        item_details['timestamp'] = int(time.time())
        redis_conn.hmset(save_hash_key, item_details)
        redis_conn.expire(save_hash_key, EXPIRE_DURATION)


def save_route53_details():
    hosted_zone_details = fetch_hosted_zone_details()
    for zone_name, zone_id in hosted_zone_details.items():
        record_sets = fetch_all_route53dns_rsets(zone_id)
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
            save_dns_record(zone_name, item_details)

######## BOTO ########

def get_connection(region_name):
    try:
        conn = boto.ec2.connect_to_region(region_name=region_name,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    except Exception, e:
        print e
        conn = None
    return conn


def get_all_running_instances(region):
    conn = get_connection(region)
    running_instances = conn.get_all_instance_status()
    id_list = []
    for r in running_instances:
        id_list.append(r.id)
    reservations = conn.get_all_instances(instance_ids=id_list)
    instance_list = []
    for r in reservations:
        for i in r.instances:
            instance_list.append(i)
    return instance_list


def fetch_and_save_aws_instance_details():
    for region in REGION_LIST:
        try:
            instance_list = get_all_running_instances(region)
        except Exception as e:
            print str(e)
        save_aws_instance_details(instance_list)



def save_aws_instance_details(instance_list):
    for instance in instance_list:
        aws_dns_present = False
        details = {}
        details['instance_id'] = instance.id
        details['region'] = instance.region.name
        details['zone'] = instance.placement
        details['instance_type'] = instance.instance_type
        details['private_ip_address'] = instance.private_ip_address
        details['ip_address'] = instance.ip_address
        details['dns_name'] = instance.dns_name
        dns_details = get_dns_details(details['ip_address'])
        for hash_key, item_details in dns_details.items():
            item_details.update(details)
            item_details['timestamp'] = int(time.time())
            redis_conn.hmset(hash_key, item_details)
            redis_conn.expire(hash_key, int(item_details['ttl']))
            hash_key = hash_key.replace(':%s:' % details['ip_address'],
                                        ':%s:' % details['private_ip_address'])
            redis_conn.hmset(hash_key, item_details)
            redis_conn.expire(hash_key, int(item_details['ttl']))
            if details['dns_name'] == item_details['name']:
                aws_dns_present = True
        save_key_list = []
        if len(dns_details) == 0:
            save_key_list = [
                details['private_ip_address'],
                details['ip_address'],
                details['dns_name'],
            ]
        elif aws_dns_present is False:
            save_key_list = [
                details['dns_name'],
            ]
        for key_name in save_key_list:
            save_hash_key = HASH_PREFIX % ('-', key_name, '-', '-')
            item_details = details
            details['timestamp'] = int(time.time())
            redis_conn.hmset(save_hash_key, details)
            redis_conn.expire(save_hash_key, EXPIRE_DURATION)



def get_dns_details(hostname):
    dns_details = {}
    key_regex = HASH_PREFIX % ('*', hostname, '*', '*')
    key_list = redis_conn.keys(key_regex)
    for hash_key in key_list:
        item_details = redis_conn.hgetall(hash_key)
        dns_details[hash_key] = item_details
    return dns_details




if __name__ == '__main__':
    arguments = parse_options(OPTIONS)
    hostname = arguments.hostname
    sync = arguments.sync
    if hostname != None:
        key_regex = HASH_PREFIX % ('*', hostname, '*', '*')
        key_list = redis_conn.keys(key_regex)
        for hash_key in key_list:
            print redis_conn.hgetall(hash_key)
            print '-'*50
    if sync is not None:
        save_route53_details()
        print 'Route 53 details saved'
        fetch_and_save_aws_instance_details()
        print 'AWS Instance details saved'
