## Dikhao: A new way to look at EC2 & Route53

Dikhao is a project to cache every EC2 resource, find relations between them, and provide really fast lookups. It can be installed as a python command line utility (*pip install dikhao*), deployable in heroku and has a ready to use hubot plugin.

---

#### Sample execute examples to search details about- 'dns1.rohit.io':

* CLI command:
 * $ batao -i dns1.rohit.io
* [Hubot](https://hubot.github.com/) bot in hipchat:
 * @hubot batao dns1.rohit.io
* Heroku App:
 * http://&lt;app_name&gt;.herokuapp.com/lookup/dns1.rohit.io

#### Details displayed:

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

---

#### How to install **dikhao** as:

1. A CLI tool:
    * *dikhao* is available for installation using PyPi. Once installed, it provides two commands: *padho* and *batao*. *padho* syncs AWS details into redis and *batao* can be used for searching the same.

    (venv)$ pip install dikhao

2. A heroku app:

    $ git clone git@github.com:rohit01/dikhao.git
    $ cd dikhao
    $ heroku create {app_name} -s cedar
    $ git push heroku master
    $ heroku addons:add rediscloud --app {app_name}
    $ heroku ps:scale web=1

    * Add credentials:

    $ heroku config:set AWS_ACCESS_KEY_ID='&lt;ACCESS-KEY&gt;'
    $ heroku config:set AWS_SECRET_ACCESS_KEY='&lt;SECRET-KEY&gt;'
    $ heroku config:set REDIS_HOST='&lt;rediscloud-hostname&gt;'
    $ heroku config:set REDIS_PORT_NO='&lt;rediscloud-port&gt;'
    $ heroku config:set REDIS_PASSWORD='&lt;rediscloud-password&gt;'

3. A hubot agent:
    * Deploy *dikhao* as a heroku app
    * Add the heroku application url in [coffee script](https://github.com/rohit01/dikhao/blob/master/hubot/dikhao.coffee)
    * Integrate the coffee script in your existing hubot setup

---

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
