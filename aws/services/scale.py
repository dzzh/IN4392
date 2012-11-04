import logging
from services import aws_ec2, aws_ec2_elb
from utils import aws_utils

def scale_up(config):
    """Add one instance to the environment"""
    logger = logging.getLogger(__name__)
    logger = aws_utils.monitor_logger(logger)
    if scaling_up_possible(config):
        logger.info('Upscaling started.')
        #Launch instance
        logger.info('Launching an instance.')
        instance, _ = aws_ec2.launch_instance(config)
        #Start app
        logger.info('Performing deployment operations.')
        aws_ec2.app_predeployment(config)
        aws_ec2.deploy_app_at_instance(config,instance)
        aws_ec2.app_postdeployment(config)
        #Register instance at load balancer
        logger.info('Registering an instance at the load balancer')
        elb = aws_ec2_elb.get_load_balancer(config.get('region'),config.get('elb_name'))
        elb.register_instances([instance.id])
        #Update config
        instances = config.get_list('instances')
        instances.append(instance.id)
        config.set_list('instances',instances)
        logger.info('Upscaling completed. 1 instance of type %s is added to environment' % config.get('instance_type'))
    else:
        logger.warning('Need to scale up, but all the instances are already allocated')


def scale_down(config):
    """Remove one instance from the environment"""
    logger = logging.getLogger(__name__)
    logger = aws_utils.monitor_logger(logger)
    if not scaling_down_possible(config):
        logger.warning('Scaling down not possible, minimum number of instances is running')
    else:
        logger.info('Downscaling started.')
        #Get ID of last started instance
        instance = config.get_list('instances')[-1]
        #Deregister it from load balancer
        elb = aws_ec2_elb.get_load_balancer(config.get('region'),config.get('elb_name'))
        elb.deregister_instances([instance])
        #terminate
        aws_ec2.terminate_instances([instance])
        #Update config
        instances = config.get_list('instances')
        instances.remove(instance)
        config.set_list('instances',instances)
        logger.info('Downscaling completed. 1 instance terminated.')


def scaling_up_possible(config):
    """Return true if the environment can scale up, false otherwise"""
    num_running_instances = len(config.get_list('instances'))
    max_instances = config.getint('max_instances')
    print 'UP - Num: %d, max: %d' % (num_running_instances, max_instances)
    if num_running_instances < max_instances:
        return True
    return False


def scaling_down_possible(config):
    """Return true if the environment can scale down, false otherwise"""
    num_running_instances = len(config.get_list('instances'))
    min_instances = config.getint('min_instances')
    print 'DW - Num: %d, min: %d' % (num_running_instances, min_instances)
    if num_running_instances > min_instances:
        return True
    return False
