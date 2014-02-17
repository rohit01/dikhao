import os

## AWS Credentials
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')

## Redis settings
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT_NO = os.environ.get('REDIS_PORT_NO')
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

## Application port
PORT = int(os.environ.get('PORT', 5000))

## Route53 hosted zone named separated by comma
HOSTED_ZONES = 'all'

## EC2 region to be synced (comma separated values)
REGIONS = 'all'

## Redis key expiry settings
EXPIRE_DURATION = 86400
TTL = False

## Set as True if you dont want to sync both
NO_EC2 = False
NO_ROUTE53 = False
