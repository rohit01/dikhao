from boto.route53.connection import Route53Connection


class Route53Handler(object):
    def __init__(self, apikey, apisecret):
        self.connection = Route53Connection(aws_access_key_id=apikey,
                                            aws_secret_access_key=apisecret)

    def fetch_route53_zone_details(self, hosted_zones=None):
        if (not hosted_zones) or (hosted_zones == 'all'):
            zone_list = []
        else:
            zone_list = [zone.strip() for zone in
                hosted_zones.lower().split(',')]
        hosted_zone_details = {}
        route53_zones = self.connection.get_all_hosted_zones()
        for zone in route53_zones['ListHostedZonesResponse']['HostedZones']:
            zone_id = zone['Id'].split('/')[-1]
            zone_name = zone['Name']
            if (not zone_list) or (zone_name in zone_list) or \
                    (zone_name[:-1] in zone_list):
                hosted_zone_details[zone_name] = zone_id
        return hosted_zone_details

    def fetch_all_route53dns_rsets(self, zone_id):
        record_sets = self.connection.get_all_rrsets(zone_id)
        rsets = record_sets
        while rsets.is_truncated is True:
            next_record_name = rsets.next_record_name
            next_record_type = rsets.next_record_type
            rsets = self.connection.get_all_rrsets(zone_id,
                name=next_record_name, type=next_record_type)
            record_sets.extend(rsets)
        return record_sets
