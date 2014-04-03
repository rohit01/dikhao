## Dikhao: A new way to look at EC2 & Route53

Dikhao is a project to map every EC2 resource will all related components and provide really fast lookups for the same.

### Sample run with hubot plugin:

*@hubot batao dns1.rohit.io*

<pre>
Route53 Details (210 secs ago):
+--------------------+-----+-----------+----------------------------------------------------+
| Name               | ttl | Type      | Value                                              |
+--------------------+-----+-----------+----------------------------------------------------+
| route53.rohit.io.  | 300 | CNAME     | ec2-54-162-144-108.us-west-1.compute.amazonaws.com |
| elb1-dns.rohit.io. | 600 | A (Alias) | blog-elb-993346533.us-west-1.elb.amazonaws.com.    |
| elb1-dns.rohit.io. | 600 | A (Alias) | web-elb-1401441163.us-west-1.elb.amazonaws.com.    |
+--------------------+-----+-----------+----------------------------------------------------+
EC2 Instance Details (265 secs ago):
+--------------------+----------------------------------------------------+
|           Property | Value                                              |
+--------------------+----------------------------------------------------+
|        Instance ID | i-e68e0cca                                         |
|              State | running                                            |
|            EC2 DNS | ec2-54-162-144-108.us-west-1.compute.amazonaws.com |
|         IP address | 54.162.144.108                                     |
|             Region | us-west-1                                          |
|               Zone | us-west-1b                                         |
|      Instance type | m1.large                                           |
| Private IP address | 10.201.136.202                                     |
|        Private DNS | ip-10-201-136-202.us-west-1.compute.internal       |
|          ELB names | blog-elb,web-elb                                   |
+--------------------+----------------------------------------------------+
Elastic IP Details (261 secs ago):
+----------------+-------------+
| Elastic IP     | Instance ID |
+----------------+-------------+
| 54.162.144.108 | i-e68e0cca  |
+----------------+-------------+
ELB Details (266 secs ago):
+----------+-------------------------------------------------+-------------+--------------+
| Name     | ELB DNS                                         | Instance ID | State        |
+----------+-------------------------------------------------+-------------+--------------+
| blog-elb | blog-elb-993346533.us-west-1.elb.amazonaws.com. | i-e68e0cca  | InService    |
|          |                                                 | i-e68kkbba  | InService    |
|          |                                                 | i-52641cad  | OutOfService |
| web-elb  | web-elb-1401441163.us-west-1.elb.amazonaws.com. | i-e68e0cca  | InService    |
|          |                                                 | i-e68kkbba  | InService    |
|          |                                                 | i-52641cad  | OutOfService |
+----------+-------------------------------------------------+-------------+--------------+
</pre>



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
3. ~~Heroku deployment support~~
4. ~~hubot integration~~
5. ~~setup.py installation file~~
6. ~~Grabbing a space in pip repository~~
7. Great documentation
8. *Release and plan new features!*
9. S3 sync and lookups

** Instructions will be added soon **
