import argparse
import logging
import time
from services import aws_cw, scale, aws_ec2_elb, aws_ec2
from utils import static
from utils.config import Config

unhealthy_instances = dict()

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Monitors the state of AWS environment and does autoscaling.')
    parser.add_argument('-e', '--eid', type=int, default=0, help='Environment ID')
    parser.add_argument('-n','--noscale',action='store_true',help='Prevent autoscaling.')
    return parser.parse_args()


def validate_args(args, config):
    """Validate correctness of command-line args"""
    if not args.eid:
        print 'You should specify environment id to delete it'
        exit(1)

    if not config.has_section(str(args.eid)):
        print 'The environment with the specified id does not exist'
        exit(1)

    if args.eid and (args.eid < 100 or args.eid > 999):
        print 'ID should be in range [100,1000)'
        exit(1)


def process_instance_state(config, state):
    if config.get_list('instances').contains(state['InstanceId']) and \
       not state['state'] == 'InService' and \
       not state['reason'] == 'Instance registration is still in progress.':
        id = state['InstanceId']
        if unhealthy_instances.has_key(id):
            num_checks = unhealthy_instances.get(id)
            if num_checks + 1 == static.HEALTH_CHECKS:
                logger.info('Stopping unhealty instance %s for investigation' %id)
                unhealthy_instances.pop(id)
                #Instance is considered failed and should be stopped for investigation
                #Deregister it from load balancer
                elb = aws_ec2_elb.get_load_balancer(config.get('region'),config.get('elb_name'))
                elb.deregister_instances([id])
                #stop it
                instance = aws_ec2.get_instance(config,id)
                instance.stop()
                #Update config
                instances = config.get_list('instances')
                instances.remove(id)
                config.set_list('instances',instances)
                logger.info('Unhealthy instance is successfully stopped. ')
                logger.info('A new instance instead of stopped one will be allocated automatically.')
            else:
                unhealthy_instances[id] = num_checks + 1
        else:
            unhealthy_instances[id] = 1
            logger.warning('Instance %s is unhealthy with state %s and code %s' %(id, state['Status'], state['ReasonCode']))
            logger.warning('After %s checks it will be stopped.' % static.HEALTH_CHECKS)

if __name__ == '__main__':
    config = Config()
    args = parse_args()
    validate_args(args,config)
    config.env_id = str(args.eid)

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO, filename=config.get_home_dir() + 'monitor.log')
    logger = logging.getLogger(__name__)

    while True:

        #Autoscaling
        avg_cpu = aws_cw.get_avg_cpu_utilization_percentage_for_environment(config)
        logger.info('Current CPU utilization for the environment %s is %.2f percent'
                        % (config.env_id, avg_cpu))

        if avg_cpu > static.AUTOSCALE_CPU_PERCENTAGE_UP:
            if not args.noscale:
                if scale.scaling_up_possible(config):
                    scale.scale_up(config)
                else:
                    logger.warning('The environment has exceeded scaling capacity but further scaling needed.')
            else:
                logger.warning('The environment is highly loaded, scaling needed.')

        elif avg_cpu < static.AUTOSCALE_CPU_PERCENTAGE_DOWN:
            if not args.noscale:
                if scale.scaling_down_possible(config):
                    scale.scale_down(config)
            else:
                if scale.scaling_down_possible(config):
                    logger.info('The load on the environment is low, downscaling is possible.')

        #Health check
        elb = aws_ec2_elb.get_load_balancer(config.get('region'),config.get('elb_name'))
        instance_states = elb.get_instance_health()
        for instance_state in instance_states:
            process_instance_state(config, instance_state)

        time.sleep(static.MONITOR_SLEEP_TIME)