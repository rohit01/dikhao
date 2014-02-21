#!/usr/bin/env python
#
# Utility to sync route53, ec2 details in redis.
# This program should be deployed as a cron job with high frequency.
#
# Author - @rohit01

from dikhao.sync import *

if __name__ == '__main__':
    option_args = util.parse_options(options=OPTIONS,
        flag_options=FLAG_OPTIONS, description=DESCRIPTION, usage=USAGE,
        version=VERSION)
    arguments = validate_arguments(option_args)
    route53_handler = dikhao.aws.route53.Route53Handler(apikey=arguments['apikey'],
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
