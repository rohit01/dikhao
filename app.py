# -*- coding: utf-8 -*-
#
# Python flask application to be deployed as a heroku application
# Author - @rohit01

import os
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


def sync_everything():
    redis_handler = database.redis_handler.RedisHandler(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT_NO
    )
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
    gevent.joinall(thread_list, timeout=120)
    print 'Cleanup stale records initiated...'
    sync.clean_stale_entries(redis_handler,
                             clean_route53=not config.NO_ROUTE53,
                             clean_ec2=not config.NO_EC2)
    print 'Details saved. Indexing records!'
    sync.index_records(redis_handler, expire=config.EXPIRE_DURATION)
    print 'Complete'


@app.route("/sync", methods=['GET', 'POST'])
def sync_details():
    """
    Sync AWS details into redis and reply status
    """
    gevent.spawn_raw(sync_everything)
    return 'OK'


@app.route('/lookup/<input_lookup>', methods=['GET', 'POST'])
def search(input_lookup):
    """
    Perform lookup for given input in redis database
    """
    redis_handler = database.redis_handler.RedisHandler(host=config.REDIS_HOST,
        port=config.REDIS_PORT_NO)
    match_dict = lookup.search(redis_handler, host=input_lookup)
    if match_dict:
        details = lookup.formatted_output(redis_handler, match_dict)
        return "<HTML><HEAD></HEAD><BODY><PRE>%s</PRE></BODY></HTML>" \
                % lookup.string_details(details)
    else:
        return 'Sorry! No entry found'


@app.route("/config", methods=['GET', 'POST'])
def config_details():
    """
    Return config details for verification
    """
    config_list = []
    config_list.append("AWS_ACCESS_KEY_ID: %s" % config.AWS_ACCESS_KEY_ID[:5])
    config_list.append("AWS_SECRET_ACCESS_KEY: %s" %
                       config.AWS_SECRET_ACCESS_KEY[:5])
    config_list.append("REDIS_HOST: %s" % config.REDIS_HOST[:5])
    config_list.append("REDIS_PORT_NO: %s" % config.REDIS_PORT_NO[:5])
    config_list.append("HOSTED_ZONES: %s" % config.HOSTED_ZONES)
    config_list.append("REGIONS: %s" % config.REGIONS)
    config_list.append("EXPIRE_DURATION: %s" % config.EXPIRE_DURATION)
    config_list.append("TTL: %s" % config.TTL)
    config_list.append("NO_EC2: %s" % config.NO_EC2)
    config_list.append("NO_ROUTE53: %s" % config.NO_ROUTE53)
    return "<HTML><HEAD></HEAD><BODY><PRE>%s</PRE></BODY></HTML>" \
           % '\n'.join(config_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
