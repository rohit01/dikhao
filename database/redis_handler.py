import redis
import time
import socket


def resolve_dns_to_ip(hostname):
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None


class RedisHandler(object):
    def __init__(self, host=None, port=None, expire=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 6379
        if expire == 0:
            expire = None
        self.connection = redis.StrictRedis(host, port)
        self.expire = expire
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
