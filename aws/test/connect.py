import os
from boto.ec2 import instance
import boto.manage.cmdshell
from utils import aws_utils,static

if __name__ == '__main__':
    config = aws_utils.get_config()
    ec2 = boto.ec2.connect_to_region(config.get('environment','region'))
    instance = ec2.get_all_instances(filters = {'instance-state-name':'running'})[0].instances[0]
    print instance.id

    key_path = os.path.join(os.path.expanduser(static.KEY_DIR), key_name+static.KEY_EXTENSION)
    cmd = boto.manage.cmdshell.sshclient_from_instance(instance, key_path, user_name= 'ec2-user')

    print cmd
