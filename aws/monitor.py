import argparse
import logging
import threading
import time
import datetime
from services import aws_cw, scale, aws_ec2_elb, aws_ec2
from utils import static
from utils.config import Config

unhealthy_instances = dict()
next_scale_allowed = datetime.datetime.now()

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
    if state.instance_id in config.get_list('instances') and \
       not state.state == 'InService' and \
       not state.reason_code == 'Instance registration is still in progress.' and \
       not state.reason_code == 'ELB':
        id = state.instance_id
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
            logger.warning('Instance %s is unhealthy with state %s and code %s' %(id, state.state, state.reason_code))
            logger.warning('After %s checks it will be stopped.' % static.HEALTH_CHECKS)


def set_next_possible_scaling_time():
    global next_scale_allowed
    now = datetime.datetime.now()
    duration = datetime.timedelta(seconds = static.AUTOSCALE_DELAY_AFTER_SCALING)
    next_scale_allowed = now + duration


def is_upscaling_allowed(config):
    '''Allow upsaling only if we have 2+ statistics records for the recently added instance.
       Is needed to prevent too agressive upscaling'''
    latest_launched_instance_id = config.get_list('instances')[-1]
    logger.info('id %s'%latest_launched_instance_id)
    num = aws_cw.get_num_records_for_instance(config,latest_launched_instance_id)
    logger.info('Num statistical records for latest instance %s is %d' %(latest_launched_instance_id,num))
    logger.info(next_scale_allowed)
    return num > 1 and \
           datetime.datetime.now() > next_scale_allowed


def is_downscaling_allowed():
    return datetime.datetime.now() > next_scale_allowed


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
                    if is_upscaling_allowed(config):
                        threading.Thread(target=scale.scale_up, args=(config,)).start()
                        set_next_possible_scaling_time()
                    else:
                        logger.info('Next upscaling is deferred until getting statistics from a newly added instance.')
                else:
                    logger.warning('The environment has exceeded scaling capacity but further scaling needed.')
            else:
                logger.warning('The environment is highly loaded, scaling needed.')

        elif avg_cpu < static.AUTOSCALE_CPU_PERCENTAGE_DOWN:
            if not args.noscale:
                if scale.scaling_down_possible(config):
                    if is_downscaling_allowed():
                        threading.Thread(target=scale.scale_down, args=(config,)).start()
                        set_next_possible_scaling_time()
                    else:
                        logger.info('Next downscaling is deferred until getting statistics from an updated environment.')
            else:
                if scale.scaling_down_possible(config):
                    logger.info('The load on the environment is low, downscaling is possible.')

        #Health check
        elb = aws_ec2_elb.get_load_balancer(config.get('region'),config.get('elb_name'))
        instance_states = elb.get_instance_health()
        for instance_state in instance_states:
            process_instance_state(config, instance_state)
        logger.info('Start waiting')
        time.sleep(static.MONITOR_SLEEP_TIME)
        logger.info('Stop waiting')