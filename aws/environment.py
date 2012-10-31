import argparse
import os
import random
import boto
import boto.manage.cmdshell
from services import aws_ec2
from utils import aws_utils, static, commands

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Performs operations with AWS environments.')
    parser.add_argument('operation', metavar='op', type=str, choices=['create', 'delete', 'deploy'],
        help='Operation on environment, create, delete or deploy')
    parser.add_argument('-e', '--eid', type=int, default=0, help='Environment ID')
    parser.add_argument('-n', '--noconnect', help='Omits connection test to the newly created instance for speedup.')
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


def create_environment(env_id, config, connect):
    """Create a new environment given its config and ID"""
    if env_id == '0':
        while env_id == '0' or config.has_section(env_id):
            env_id = str(random.randrange(100,1000))

    #Launch instances
    config.add_section(env_id)
    launch = aws_ec2.launch_instance(connect)
    config.set(env_id,'instances',launch[0].id)
    print 'Created environment with id %s' % env_id
    return config


def delete_environment(env_id, config):
    """Delete an environment given its ID"""
    instances = config.get(env_id,'instances').split(',')
    aws_ec2.terminate_instances(instances)
    config.remove_section(env_id)
    print 'Environment %s deleted, %d instance(s) terminated' %(env_id, len(instances))
    return config


def deploy_app(env_id, config):

    #Zip the job
    aws_utils.prepare_archives()
    print 'Job and remote configuration are prepared for deployment'

    job_archive_file = static.JOB_BASE_NAME+'.'+static.ARCHIVE_FORMAT
    config_archive_file = static.RC_BASE_NAME+'.'+static.ARCHIVE_FORMAT
    key_name = config.get('environment','key_name')

    #Transfer the archives to the instances
    instances = aws_ec2.get_running_instances(env_id)
    key_path = os.path.join(os.path.expanduser(static.KEY_DIR), key_name + static.KEY_EXTENSION)
    login_user = config.get('environment','login_user')
    local_job_path = os.path.abspath(job_archive_file)
    remote_job_path = '/home/%s/.deploy/job/%s' % (login_user,job_archive_file)
    local_config_path = os.path.abspath(config_archive_file)
    remote_config_path = '/home/%s/.deploy/config/%s' % (login_user,config_archive_file)

    for instance in instances:
        cmd = boto.manage.cmdshell.sshclient_from_instance(instance, key_path, user_name=login_user)
        aws_utils.run_command(cmd, commands.PRE_DEPLOYMENT)
        print '(%s) Pre-deployment maintenance tasks completed' % instance.id

        cmd.put_file(local_job_path,remote_job_path)
        cmd.put_file(local_config_path,remote_config_path)
        print 'Updating the server and deploying the application (may take several minutes, grab a coffee)'
        aws_utils.run_pty(cmd, commands.DEPLOYMENT %(config_archive_file, login_user, login_user))
        print '(%s) Deployment maintenance task completed.' % instance.id
        print 'Public DNS: %s' %instance.public_dns_name

    print 'Deployment completed for %d instance(s)' % len(instances)

    os.remove(job_archive_file)
    os.remove(config_archive_file)


if __name__ == '__main__':
    config = aws_utils.read_config()
    args = parse_args()
    validate_args(args, config)

    env_id = str(args.eid)
    if args.operation == 'create':
        config = create_environment(env_id, config, not args.noconnect)

    if args.operation == 'delete':
        config = delete_environment(env_id, config)

    if args.operation == 'deploy':
        deploy_app(env_id, config)

    aws_utils.write_config(config)

