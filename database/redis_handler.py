import redis

class RedisHandler(object):
    def __init__(self, host=None, port=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 6379
        self.connection = redis.StrictRedis(host, port)
        self.route53_hash_prefix = 'aws:route53'         ## Suffix: Type, name
        self.ec2_hash_prefix = 'aws:ec2'        ## Suffix: region, instance id
        self.index_prefix = 'aws:index'         ## Suffix: index_item

    def save_route53_details(self, item_details):
        hash_key = "%s:%s:%s" % (self.route53_hash_prefix,
                                 item_details['type'], item_details['name'])
        status = self.connection.hmset(hash_key, item_details)
        return (hash_key, status)

    def save_ec2_details(self, item_details):
        hash_key = "%s:%s:%s" % (self.ec2_hash_prefix, item_details['region'],
                                 item_details['instance_id'])
        status = self.connection.hmset(hash_key, item_details)
        return (hash_key, status)

    def delete_ec2_details(self, region, instance_id):
        hash_key = "%s:%s:%s" % (self.ec2_hash_prefix, region, instance_id)
        status = self.connection.delete(hash_key) == 1  ## Returns 1 if deleted
        return (hash_key, status)

    def get_details(self, hash_key):
        return self.connection.hgetall(hash_key)

    def save_index(self, key, value):
        hash_key = "%s:%s" % (self.index_prefix, key)
        status = self.connection.set(hash_key, value)
        return (hash_key, status)

    def get_index(self, key):
        hash_key = "%s:%s" % (self.index_prefix, key)
        return self.connection.get(hash_key)

    def delete_index(self, key):
        hash_key = "%s:%s" % (self.index_prefix, key)
        return self.connection.delete(hash_key)

    def exists(self, hash_key):
        return self.connection.exists(hash_key)
