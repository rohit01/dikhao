# -*- coding: utf-8 -*-
#
# Python flask application to be deployed as a heroku application
# Author - @rohit01

import os
import config
import lookup
import sync
import database
from flask import Flask


app = Flask(__name__)

@app.route("/")
def status():
    """
    Returns the status page
    """
    return 'OK'


@app.route("/sync_aws", methods=['GET', 'POST'])
def sync_aws():
    """
    Syncs AWS information into redis and replies status
    """
    ## TODO
    return 'TODO'


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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
