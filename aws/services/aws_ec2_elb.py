import ConfigParser
import boto.ec2.elb
from utils import aws_utils
from boto.ec2.elb import HealthCheck

def create_load_balancer(zones,env_id):
    config = aws_utils.read_config()

    if config.has_section(env_id):
        name = config.get(env_id,'elb_name')
        if name:
            print ('A load balancer already exists for this environment')
            exit(1)

    region = config.get('environment','region')
    conn = boto.ec2.elb.connect_to_region(region)
    ports = [(80,80, 'http')]

    hc_res = config.get('environment','health_check_resource')
    hc = HealthCheck(
        interval=30,
        healthy_threshold=3,
        unhealthy_threshold=5,
        target='HTTP:80/%s' %hc_res
    )

    name = 'lb-%s' %env_id
    elb = conn.create_load_balancer(name, zones, ports)
    elb.configure_health_check(hc)
    return name, elb


def get_load_balancer(region, name):
    conn = boto.ec2.elb.connect_to_region(region)
    lbs = conn.get_all_load_balancers(load_balancer_names=[name])
    if not lbs:
        print 'Load balancer with name %s not found in region %s' % (name, region)
    else:
        return lbs[0]

