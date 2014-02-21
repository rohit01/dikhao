#!/usr/bin/env python
#
# Program to perform dns and reverse dns lookup from locally synced redis DB.
#
# Author - @rohit01

from dikhao.lookup import *

if __name__ == '__main__':
    option_args = util.parse_options(options=OPTIONS, description=DESCRIPTION,
        usage=USAGE, version=VERSION)
    arguments = validate_arguments(option_args)
    redis_handler = dikhao.database.redis_handler.RedisHandler(
        host=arguments['redis_host'], port=arguments['redis_port_no'])
    match_dict = search(redis_handler, host=arguments['input_lookup'])
    if match_dict:
        details = formatted_output(redis_handler, match_dict)
        print string_details(details)
    else:
        print 'Sorry! No entry found'
        sys.exit(1)
