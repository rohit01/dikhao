import redis

class RedisHandler(object):
    def __init__(self, host=None, port=None):
        if host is None:
            host = '127.0.0.1'
        if port is None:
            port = 6379
        self.connection = redis.StrictRedis(host, port)
        self.route53_hash_prefix = 'aws:route53:%s:%s'   ## Type, name
        self.ec2_hash_prefix = 'aws:ec2:%s:%s'           ## region, instance id

    def save_route53_details(self, item_details):
        hash_key = self.route53_hash_prefix % (item_details['type'], item_details['name'])
        self.connection.hmset(hash_key, item_details)

    def save_ec2_details(self, item_details):
        hash_key = self.ec2_hash_prefix % (item_details['region'], item_details['instance_id'])
        self.connection.hmset(hash_key, item_details)

    def delete_ec2_details(self, region, instance_id):
        hash_key = self.ec2_hash_prefix % (region, instance_id)
        self.connection.delete(hash_key)
