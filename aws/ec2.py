######## BOTO ########

def get_connection(region_name):
    try:
        conn = boto.ec2.connect_to_region(region_name=region_name,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    except Exception, e:
        print e
        conn = None
    return conn


def get_all_running_instances(region):
    conn = get_connection(region)
    running_instances = conn.get_all_instance_status()
    id_list = []
    for r in running_instances:
        id_list.append(r.id)
    reservations = conn.get_all_instances(instance_ids=id_list)
    instance_list = []
    for r in reservations:
        for i in r.instances:
            instance_list.append(i)
    return instance_list


def fetch_and_save_aws_instance_details():
    for region in REGION_LIST:
        try:
            instance_list = get_all_running_instances(region)
        except Exception as e:
            print str(e)
        save_aws_instance_details(instance_list)
