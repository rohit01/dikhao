## Dikhao: A new way to look at EC2 & Route53

Dikhao is a project to map every EC2 resource will all related components and provide really fast lookups for the same. This project is under active development.

#### Current features:
1. Sync all Route53 records in redis
2. Sync all EC2 instance records in redis
3. Sync all ELB records in redis
4. Index all synced records
5. Provides variety of syncing options like cache expire based on ttl/duration.
6. Easy and fast lookups based on: ip address, private ip, instance id, route 53 DNS, ec2 dns, etc. And this list is configurable.

#### Planned features:
1. ~~Sync and lookup for elastic ip~~
2. Sync and lookup for VPC
3. Heroku deployment support
4. hubot integration
5. ~~setup.py installation file~~
6. ~~Grabbing a space in pip repository~~
7. Great documentation
8. *Release and plan new features!*

** Instructions will be added soon **
