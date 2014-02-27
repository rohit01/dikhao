# -*- coding: utf-8 -*-
#
# Python flask application to be deployed as a heroku application
# Author - @rohit01

import os
import time
import redis
import gevent
import config
import dikhao.search
import dikhao.sync
import dikhao.database
import dikhao.aws.route53
from flask import Flask
from setup import VERSION


app = Flask(__name__)
redis_handler = dikhao.database.redis_handler.RedisHandler(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT_NO,
    password=config.REDIS_PASSWORD,
    timeout=config.REDIS_TIMEOUT,
    max_connections=config.REDIS_MAX_CONNECTIONS,
)


@app.route("/")
def status():
    """
    Returns the status page
    """
    return 'Ok - Version: %s' % VERSION


def sync_everything():
    try:
        redis_handler.close_extra_connections()
        thread_list = []
        if not config.NO_ROUTE53:
            route53_handler = dikhao.aws.route53.Route53Handler(
                apikey=config.AWS_ACCESS_KEY_ID,
                apisecret=config.AWS_SECRET_ACCESS_KEY)
            new_threads = dikhao.sync.sync_route53(route53_handler, redis_handler,
                config.HOSTED_ZONES, expire=config.EXPIRE_DURATION, ttl=config.TTL)
            thread_list.extend(new_threads)
        if not config.NO_EC2:
            new_threads = dikhao.sync.sync_ec2(redis_handler, apikey=config.AWS_ACCESS_KEY_ID,
                apisecret=config.AWS_SECRET_ACCESS_KEY, regions=config.REGIONS,
                expire=config.EXPIRE_DURATION)
            thread_list.extend(new_threads)
        print 'Sync Started... . . .  .  .   .     .     .'
        gevent.joinall(thread_list, timeout=config.SYNC_TIMEOUT)
        gevent.killall(thread_list)
        print 'Cleanup stale records initiated...'
        dikhao.sync.clean_stale_entries(redis_handler,
                                 clean_route53=not config.NO_ROUTE53,
                                 clean_ec2=not config.NO_EC2)
        print 'Details saved. Indexing records!'
        dikhao.sync.index_records(redis_handler, expire=config.EXPIRE_DURATION)
        redis_handler.delete_lock(timeout=config.MIN_SYNC_GAP)
    except redis.ConnectionError:
        print 'Redis ConnectionError happened. Closing all active connections'
        redis_handler.close_extra_connections(max_connections=0)
    print 'Complete'


@app.route("/sync", methods=['GET', 'POST'])
def sync_details():
    """
    Sync AWS details into redis and reply status
    """
    lock_time, expire_timeout = redis_handler.get_lock()
    if lock_time in ['0', 0]:
        expire_timeout = expire_timeout if expire_timeout else 0
        return "Synced recently. It can be started again after %s secs" \
               % expire_timeout
    elif lock_time:
        return "Sync in progress. Started %s secs ago" \
               % (int(time.time()) - int(lock_time))
    else:
        if config.SYNC_LOCK:
            timeout = config.SYNC_TIMEOUT + config.MIN_SYNC_GAP
            redis_handler.save_lock(timeout=timeout)
        gevent.spawn_raw(sync_everything)
    return 'OK - Sync initiated'


@app.route('/lookup/<input_lookup>', methods=['GET', 'POST'])
def search(input_lookup):
    """
    Perform lookup for given input in redis database
    """
    try:
        redis_handler.close_extra_connections()
        match_dict = dikhao.search.search(redis_handler, host=input_lookup)
        if match_dict:
            details = dikhao.search.formatted_output(redis_handler, match_dict)
            return dikhao.search.string_details(details)
    except redis.ConnectionError:
        print 'Redis ConnectionError happened. Closing all active connections'
        redis_handler.close_extra_connections(max_connections=0)
    return 'Sorry! No entry found'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG)
