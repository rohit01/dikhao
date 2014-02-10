import boto.ec2

def get_region_list():
    regions = boto.ec2.get_regions('ec2')
    return [r.name for r in regions]


class Ec2Handler(object):
    def __init__(self, apikey, apisecret, region):
        self.region = region
        self.connection = boto.ec2.connect_to_region(
            region_name=self.region,
            aws_access_key_id=apikey,
            aws_secret_access_key=apisecret
        )

    def get_all_running_instances(self):
        running_instances = self.connection.get_all_instance_status()
        id_list = []
        for r in running_instances:
            id_list.append(r.id)
        reservations = self.connection.get_all_instances(instance_ids=id_list)
        instance_list = []
        for r in reservations:
            for i in r.instances:
                instance_list.append(i)
        return instance_list
