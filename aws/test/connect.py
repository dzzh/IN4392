import os
from boto.ec2 import instance
import boto.manage.cmdshell
from utils import aws_utils

if __name__ == '__main__':
    cmd = None
    config = aws_utils.get_config()
    ec2 = boto.ec2.connect_to_region(config.get('environment','region'))
    instance = ec2.get_all_instances(filters = {'instance-state-name':'running'})[0].instances[0]
    print instance.id

    key_path = '/Users/zmicier/.ssh/zmicier-aws.pem'
    cmd = boto.manage.cmdshell.sshclient_from_instance(instance, key_path, user_name= 'ec2-user')

    print cmd
