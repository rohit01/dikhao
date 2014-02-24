import redis
import time


class RedisHandler(object):
    def __init__(self, host=None, port=None, password=None, timeout=None,
                 max_connections=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 6379
        self.max_connections = max_connections
        self.connection = redis.Redis(host=host, port=port, password=password,
            socket_timeout=timeout)
        self.route53_hash_prefix = 'aws:route53'             ## Suffix: Type, name
        self.instance_hash_prefix = 'aws:ec2:instance'       ## Suffix: region, instance id
        self.elb_hash_prefix = 'aws:ec2:elb'                 ## Suffix: region, elb name
        self.elastic_ip_hash_prefix = 'aws:ec2:elastic_ip'   ## Suffix: ip_address
        self.index_prefix = 'aws:index'                      ## Suffix: index_item
        self.lock_hash_key = 'dikhao:lock_sync'

    def close_extra_connections(self):
        client_list = self.connection.client_list()
        if len(client_list) < (self.max_connections - 1):
            return
        age_address_mapping = {}
        for client in client_list:
            age_address_mapping[int(client['age'])] = client['addr']
        age_list = age_address_mapping.keys()
        age_list.sort(reverse=True)
        for age in age_list:
            self.connection.client_kill(age_address_mapping[age])
            if len(self.connection.client_list()) < (self.max_connections - 1):
                return

    def save_route53_details(self, item_details):
        hash_key = "%s:%s:%s" % (self.route53_hash_prefix,
                                 item_details['type'], item_details['name'])
        status = self.connection.hmset(hash_key, item_details)
        return (hash_key, status)

    def clean_route53_entries(self, valid_keys):
        for hash_key in self.connection.keys("%s*" % self.route53_hash_prefix):
            if hash_key not in valid_keys:
                self.connection.delete(hash_key)

    def save_instance_details(self, item_details):
        hash_key = "%s:%s:%s" % (self.instance_hash_prefix,
                                 item_details['region'],
                                 item_details['instance_id'])
        status = self.connection.hmset(hash_key, item_details)
        return (hash_key, status)

    def add_instance_details(self, region, instance_id, key, value):
        hash_key = "%s:%s:%s" % (self.instance_hash_prefix, region,
                                 instance_id)
        status = self.connection.hset(hash_key, key, value)
        return (hash_key, status)

    def get_instance_item_value(self, region, instance_id, key):
        hash_key = "%s:%s:%s" % (self.instance_hash_prefix, region,
                                 instance_id)
        return self.connection.hget(hash_key, key)

    def clean_instance_entries(self, valid_keys):
        for hash_key in self.connection.keys("%s*" % self.instance_hash_prefix):
            if hash_key not in valid_keys:
                self.connection.delete(hash_key)

    def save_elb_details(self, item_details):
        hash_key = "%s:%s:%s" % (self.elb_hash_prefix,
                                 item_details['region'],
                                 item_details['elb_name'])
        status = self.connection.hmset(hash_key, item_details)
        return (hash_key, status)

    def clean_elb_entries(self, valid_keys):
        for hash_key in self.connection.keys("%s*" % self.elb_hash_prefix):
            if hash_key not in valid_keys:
                self.connection.delete(hash_key)

    def save_elastic_ip_details(self, item_details):
        hash_key = "%s:%s" % (self.elastic_ip_hash_prefix,
                              item_details['elastic_ip'])
        status = self.connection.hmset(hash_key, item_details)
        return (hash_key, status)

    def clean_elastic_ip_entries(self, valid_keys):
        for hash_key in self.connection.keys("%s*" %
                                             self.elastic_ip_hash_prefix):
            if hash_key not in valid_keys:
                self.connection.delete(hash_key)

    def get_details(self, hash_key):
        return self.connection.hgetall(hash_key)

    def save_index(self, key, value):
        hash_key = "%s:%s" % (self.index_prefix, key)
        status = self.connection.set(hash_key, value)
        return (hash_key, status)

    def expire_index(self, key, duration):
        hash_key = "%s:%s" % (self.index_prefix, key)
        return self.connection.expire(hash_key, duration)

    def get_index(self, key):
        hash_key = "%s:%s" % (self.index_prefix, key)
        return self.connection.get(hash_key)

    def get_index_hash_key(self, key):
        return "%s:%s" % (self.index_prefix, key)

    def delete_index(self, key):
        hash_key = "%s:%s" % (self.index_prefix, key)
        return self.connection.delete(hash_key)

    def save_lock(self, timeout):
        ## Set lock message as current timestamp
        self.connection.set(self.lock_hash_key, str(int(time.time())))
        self.connection.expire(self.lock_hash_key, timeout)

    def get_lock(self):
        return (self.connection.get(self.lock_hash_key),
                self.connection.ttl(self.lock_hash_key))

    def delete_lock(self, timeout=0):
        self.connection.set(self.lock_hash_key, '0')
        self.connection.expire(self.lock_hash_key, timeout)

    def exists(self, hash_key):
        return self.connection.exists(hash_key)

    def expire(self, hash_key, duration):
        return self.connection.expire(hash_key, duration)
