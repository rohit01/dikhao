import redis
import time
import socket


def resolve_dns_to_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


class RedisHandler(object):
    def __init__(self, host=None, port=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 6379
        self.connection = redis.StrictRedis(host, port)
        self.hash_prefix = 'AWS:Route53:%s:%s:%s:%s'

    def save_dns_record(self, zone_name, item_details):
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
            save_hash_key = self.hash_prefix % (zone_name, key, name, dns_type)
            item_details['timestamp'] = int(time.time())
            self.connection.hmset(save_hash_key, item_details)

    def save_aws_instance_details(self, instance_list):
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
            dns_details = self.get_dns_details(details['ip_address'])
            for hash_key, item_details in dns_details.items():
                item_details.update(details)
                item_details['timestamp'] = int(time.time())
                self.connection.hmset(hash_key, item_details)
                # self.connection.expire(hash_key, int(item_details['ttl']))
                hash_key = hash_key.replace(':%s:' % details['ip_address'],
                                            ':%s:' % details['private_ip_address'])
                self.connection.hmset(hash_key, item_details)
                # self.connection.expire(hash_key, int(item_details['ttl']))
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
                save_hash_key = self.hash_prefix % ('-', key_name, '-', '-')
                item_details = details
                details['timestamp'] = int(time.time())
                self.connection.hmset(save_hash_key, details)
                # self.connection.expire(save_hash_key, EXPIRE_DURATION)

    def get_dns_details(self, hostname):
        dns_details = {}
        key_regex = self.hash_prefix % ('*', hostname, '*', '*')
        key_list = self.connection.keys(key_regex)
        for hash_key in key_list:
            item_details = self.connection.hgetall(hash_key)
            dns_details[hash_key] = item_details
        return dns_details
