import logging
import boto.ec2.elb
from boto.ec2.elb import HealthCheck
from utils.config import Config

def create_load_balancer(zones,env_id):
    config = Config(env_id)

    if config.has_option('elb_name'):
        output = 'A load balancer already exists for this environment'
        logging.warning(output)
        print (output)
        exit(1)

    region = config.get('region')
    conn = boto.ec2.elb.connect_to_region(region)
    ports = [(80,80, 'http')]

    hc_res = config.get('health_check_resource')
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
        output = 'Load balancer with name %s not found in region %s' % (name, region)
        logging.warning(output)
        print output
    else:
        return lbs[0]

