# -*- coding: utf-8 -*-
#
# Python flask application to be deployed as a heroku application
# Author - @rohit01

import os
import time
import gevent
import config
import lookup
import sync
import database
import aws.ec2
import aws.route53
from flask import Flask


app = Flask(__name__)

@app.route("/")
def status():
    """
    Returns the status page
    """
    return 'OK'


def sync_everything(redis_handler):
    thread_list = []
    if not config.NO_ROUTE53:
        route53_handler = aws.route53.Route53Handler(
            apikey=config.AWS_ACCESS_KEY_ID,
            apisecret=config.AWS_SECRET_ACCESS_KEY)
        new_threads = sync.sync_route53(route53_handler, redis_handler,
            config.HOSTED_ZONES, expire=config.EXPIRE_DURATION, ttl=config.TTL)
        thread_list.extend(new_threads)
    if not config.NO_EC2:
        new_threads = sync.sync_ec2(redis_handler, apikey=config.AWS_ACCESS_KEY_ID,
            apisecret=config.AWS_SECRET_ACCESS_KEY, regions=config.REGIONS,
            expire=config.EXPIRE_DURATION)
        thread_list.extend(new_threads)
    print 'Sync Started... . . .  .  .   .     .     .'
    gevent.joinall(thread_list, timeout=config.SYNC_TIMEOUT)
    gevent.killall(thread_list)
    print 'Cleanup stale records initiated...'
    sync.clean_stale_entries(redis_handler,
                             clean_route53=not config.NO_ROUTE53,
                             clean_ec2=not config.NO_EC2)
    print 'Details saved. Indexing records!'
    sync.index_records(redis_handler, expire=config.EXPIRE_DURATION)
    redis_handler.delete_lock(timeout=config.MIN_SYNC_GAP)
    print 'Complete'


@app.route("/sync", methods=['GET', 'POST'])
def sync_details():
    """
    Sync AWS details into redis and reply status
    """
    redis_handler = database.redis_handler.RedisHandler(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT_NO,
        password=config.REDIS_PASSWORD
    )
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
        gevent.spawn_raw(sync_everything, redis_handler)
    return 'OK - Sync initiated'


@app.route('/lookup/<input_lookup>', methods=['GET', 'POST'])
def search(input_lookup):
    """
    Perform lookup for given input in redis database
    """
    redis_handler = database.redis_handler.RedisHandler(host=config.REDIS_HOST,
        port=config.REDIS_PORT_NO, password=config.REDIS_PASSWORD)
    match_dict = lookup.search(redis_handler, host=input_lookup)
    if match_dict:
        details = lookup.formatted_output(redis_handler, match_dict)
        return lookup.string_details(details)
    else:
        return 'Sorry! No entry found'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.PORT, debug=True)
