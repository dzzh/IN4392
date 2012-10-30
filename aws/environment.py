import argparse
import os
import random
import boto
import boto.manage.cmdshell
from services import aws_ec2
from utils import aws_utils, static

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Performs operations with AWS environments.')
    parser.add_argument('operation', metavar='op', type=str, choices=['create', 'delete', 'deploy'],
        help='Operation on environment, create, delete or deploy')
    parser.add_argument('-e', '--eid', type=int, default=0, help='Environment ID')
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


def create_environment(env_id, config):
    """Create a new environment given its config and ID"""
    if env_id == '0':
        while env_id == '0' or config.has_section(env_id):
            env_id = str(random.randrange(100,1000))

    config.add_section(env_id)
    launch = aws_ec2.launch_instance()
    config.set(env_id,'instances',launch[0].id)
    print 'Created environment with id %s' % env_id
    return config


def delete_environment(env_id, config):
    """Delete an environment given its ID"""
    instances = config.get(env_id,'instances').split(',')
    aws_ec2.terminate_instances(instances)
    config.remove_section(env_id)
    return config


def deploy_app(env_id, config):

    #Zip the job
    aws_utils.prepare_archive()
    print 'Job is prepared for deployment'

    archive_file = static.JOB_BASE_NAME+'.'+static.ARCHIVE_FORMAT
    key_name = config.get('environment','key_name')

    #Transfer the archive to the environment instances
    instances = aws_ec2.get_running_instances(env_id)
    key_path = os.path.join(os.path.expanduser(static.KEY_DIR), key_name + static.KEY_EXTENSION)
    login_user = config.get('environment','login_user')
    local_path = os.path.abspath(archive_file)
    remote_path = '/home/%s/%s' % (login_user,archive_file)

    for instance in instances:
        cmd = boto.manage.cmdshell.sshclient_from_instance(instance, key_path, user_name=login_user)
        print 'archive: %s' %archive_file
        cmd.put_file(local_path,remote_path)
        #cmd.close() - not working
    print 'Job transferred to %d instance(s)' % len(instances)

    os.remove(archive_file)


if __name__ == '__main__':
    config = aws_utils.read_config()
    args = parse_args()
    validate_args(args, config)

    env_id = str(args.eid)
    if args.operation == 'create':
        config = create_environment(env_id, config)

    if args.operation == 'delete':
        config = delete_environment(env_id, config)

    if args.operation == 'deploy':
        deploy_app(env_id, config)

    aws_utils.write_config(config)

