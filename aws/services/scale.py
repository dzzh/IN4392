import ConfigParser
import logging
import time
from services import aws_ec2, aws_ec2_elb

def scale_up(config):
    """Add one instance to the environment"""
    logger = logging.getLogger(__name__)
    if scaling_up_possible(config):
        if scale_from_pool_possible(config):
            scale_from_pool(config)
        else:
            scale_with_new_instance(config)
        logger.info('Upscaling completed. 1 instance of type %s is added to environment' % config.get('instance_type'))
    else:
        logger.warning('Need to scale up, but all the instances are already allocated')


def scale_from_pool(config):
    logger = logging.getLogger(__name__)
    #Launch instance
    logger.info('Upscaling from the pool started.')
    stopped_instance_id = config.get_list('stopped_instances')[-1]
    instance = aws_ec2.get_instance(config,stopped_instance_id)
    instance.start()
    time.sleep(30)
    #Start httpd service
    aws_ec2.start_httpd(config,instance)
    #Register instance at load balancer
    logger.info('Registering an instance at the load balancer')
    elb = aws_ec2_elb.get_load_balancer(config.get('region'),config.get('elb_name'))
    elb.register_instances([instance.id])
    #Update config
    instances = config.get_list('stopped_instances')
    instances.remove(instance.id)
    config.set_list('stopped_instances',instances)
    instances = config.get_list('instances')
    instances.append(instance.id)
    config.set_list('instances',instances)


def scale_with_new_instance(config):
    logger = logging.getLogger(__name__)
    logger.info('Upscaling with the new instance started.')
    #Launch instance
    logger.info('Launching an instance.')
    instance, _ = aws_ec2.launch_instance()
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


def scale_from_pool_possible(config):
    try:
        stopped_instances = config.get_list('stopped_instances')
    except ConfigParser.NoOptionError:
        return False
    if len(stopped_instances) > 0:
        return True
    else:
        return False


def scale_down(config):
    """Remove one instance from the environment"""
    logger = logging.getLogger(__name__)
    if not scaling_down_possible(config):
        logger.warning('Scaling down not possible, minimum number of instances is running')
    else:
        logger.info('Downscaling started.')
        #Get ID of last started instance
        instance_id = config.get_list('instances')[-1]
        #Deregister it from load balancer
        elb = aws_ec2_elb.get_load_balancer(config.get('region'),config.get('elb_name'))
        elb.deregister_instances([instance_id])
        #stop it
        instance = aws_ec2.get_instance(config,instance_id)
        instance.stop()
        #Update config
        try:
            instances = config.get_list('stopped_instances')
        except ConfigParser.NoOptionError:
            instances = []
        instances.append(instance_id)
        config.set_list('stopped_instances',instances)
        instances = config.get_list('instances')
        instances.remove(instance_id)
        config.set_list('instances',instances)
        logger.info('Downscaling completed. 1 instance stopped and is available in the pool.')
        logger.info('%d instances are currently on duty.' % len(instances))


def scaling_up_possible(config):
    """Return true if the environment can scale up, false otherwise"""
    num_running_instances = len(config.get_list('instances'))
    max_instances = config.getint('max_instances')
    if num_running_instances < max_instances:
        return True
    return False


def scaling_down_possible(config):
    """Return true if the environment can scale down, false otherwise"""
    num_running_instances = len(config.get_list('instances'))
    min_instances = config.getint('min_instances')
    if num_running_instances > min_instances:
        return True
    return False
