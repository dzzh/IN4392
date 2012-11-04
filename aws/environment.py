import argparse
import logging
import random
import threading
from utils.config import *
from services import aws_ec2, aws_ec2_elb

instances = list()

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Performs operations with AWS environments.')
    parser.add_argument('operation', metavar='op', type=str, choices=['create', 'delete', 'deploy'],
        help='Operation on environment, create, delete or deploy')
    parser.add_argument('-e', '--eid', type=int, default=0, help='Environment ID')
    parser.add_argument('-n', '--noconnect', action='store_true',
        help='Omits connection test to the newly created instance for speedup.')
    return parser.parse_args()


def validate_args(args, config):
    """Validate command-line args"""
    if args.operation == 'delete':
        if not args.eid:
            print 'You should specify environment id to delete it'
            exit(1)

        if not config.has_section(str(args.eid)):
            print 'The environment with the specified id does not exist'
            exit(1)

    if args.operation == 'create':
        if config.has_section(str(args.eid)):
            print 'The environment with the specified id already exists'
            exit(1)

    if args.operation == 'deploy':
        if not args.eid:
            print 'You should specify environment id to deploy the application'
            exit(1)

        if not config.has_section(str(args.eid)):
            print 'The environment with the specified id does not exist, create it first'
            exit(1)

    if args.eid and (args.eid < 100 or args.eid > 999):
        print 'ID should be in range [100,1000)'
        exit(1)


def launch_instance(connect):
    """ Launch EC2 instance. Thread-safe.
        connect - whether to perform connection test (up to 1 min usually)
    """
    launch = aws_ec2.launch_instance(connect)
    l = threading.Lock()
    l.acquire()
    instances.append(launch[0].id)
    l.release()


def create_environment(env_id, config, connect):
    """ Create a new environment given its config and ID
        Connect - whether to perform connection test (up to 1 min usually)
    """
    logger = logging.getLogger(__name__)
    logger.info('Creating an environment')
    if env_id == '0':
        while env_id == '0' or config.has_section(env_id):
            env_id = str(random.randrange(100,1000))

    config.env_id = env_id
    min_instances = config.getint('min_instances')

    #Just in case
    if min_instances < 1 or min_instances > 10:
        print 'The system can only work with 1-10 instances'
        exit(1)

    #Launch instances simultaneously
    logger.info('Launching %d instances' % min_instances)
    threads = list()
    for _ in range(0,min_instances):
        threads.append(threading.Thread(target=launch_instance, args=(connect,)))

    [t.start() for t in threads]
    [t.join() for t in threads]

    config.set('instances',','.join(instances))

    #Adding a load balancer
    logger.info('Starting a load balancer')
    zones = aws_ec2.get_availability_zones()
    lb_name, lb = aws_ec2_elb.create_load_balancer([zone.name for zone in zones],env_id)
    lb.register_instances(instances)
    config.set('elb_name',lb_name)

    output = 'Created environment with id %s' % env_id
    print output
    logger.info(output)

    output = 'The environment is accessible via dns %s, but deploy an app first' %lb.dns_name
    print output
    logger.info(output)
    return config


def delete_environment(config):
    """Delete an environment given its ID"""
    logger = logging.getLogger(__name__)
    logger.info('Deleting environment %s' % config.env_id)
    instances = config.get('instances').split(',')
    try:
        stopped_instances = config.get('stopped_instances').split(',')
    except ConfigParser.NoOptionError:
        stopped_instances = []
    logger.info('Deleting load balancer')
    elb_name = config.get('elb_name')
    region = config.get('region')
    lb = aws_ec2_elb.get_load_balancer(region, elb_name)
    lb.delete()
    logger.info('Terminating instances')
    aws_ec2.terminate_instances(instances)
    if len(stopped_instances) > 0:
        aws_ec2.terminate_instances(stopped_instances)
    config.remove_section(env_id)
    output = 'Environment %s deleted, %d instance(s) terminated' %(env_id, len(instances) + len(stopped_instances))
    logger.info(output)
    print output
    return config


def deploy_app_at_environment(config):
    """Deploy an app to the environment"""
    logger = logging.getLogger(__name__)

    aws_ec2.app_predeployment(config)

    #Transfer the archives to the instances
    instances = aws_ec2.get_running_instances(config)

    threads = list()
    for instance in instances:
        threads.append(threading.Thread(target=aws_ec2.deploy_app_at_instance, args=(config,instance)))

    [t.start() for t in threads]
    [t.join() for t in threads]


    output = 'Deployment completed for %d instance(s). App may still be inaccessible for a couple of minutes' % len(instances)
    logger.info(output)
    print output


if __name__ == '__main__':
    config = Config()
    logging.basicConfig(filename=config.get_home_dir() + 'environment.log', filemode='w', level=logging.INFO)
    config = Config()
    args = parse_args()
    validate_args(args, config)

    env_id = str(args.eid)
    if args.operation == 'create':
        config = create_environment(env_id, config, not args.noconnect)

    config.env_id = env_id
    if args.operation == 'delete':
        config = delete_environment(config)

    if args.operation == 'deploy':
        deploy_app_at_environment(config)

