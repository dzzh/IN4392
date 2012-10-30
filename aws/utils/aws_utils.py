import boto.ec2

CONFIG_FILE = "aws.config"

import ConfigParser

def read_config():
    """Read config file and return ConfigParser.Config"""
    config = ConfigParser.ConfigParser()
    config.readfp(open(CONFIG_FILE))
    config.read([CONFIG_FILE])
    return config

def write_config(config):
    """Write config to the config file"""
    with open(CONFIG_FILE, 'wb') as configfile:
        config.write(configfile)

def get_console_log(instance_id):
    """Print console log of a given EC2 instance"""
    config = read_config()
    ec2 = boto.ec2.connect_to_region(config.get('environment','region'))
    reservations = ec2.get_all_instances(filters = {'instance-id':instance_id})
    if reservations:
        instance = reservations[0].instances[0]
        return instance.get_console_output().output
    else:
        return 'Instance with id %s not found' % instance_id

