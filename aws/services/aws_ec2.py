import logging
import os
import time
import boto
import boto.ec2
import boto.manage.cmdshell

from utils import static, commands, aws_utils, wsgi_conf_writer
from utils.config import Config

#empirically determined value which is sufficient for the instance
#to get ready for accepting ssh connection
CONNECTION_DELAY = 60

#The function is based on ec2_launch_instance.py from Python and AWS Cookbook
def launch_instance(connect=True):
    """Launch an instance and wait for it to start running.
    Returns a tuple consisting of the Instance object and the CmdShell object,
    if request, or None.

    -connect tells to perform the SSH connection test to the newly created instance (up to 1 min of time)
    """

    config = Config()

    # Create a connection to EC2 service (assuming credentials are in boto config)
    ec2 = boto.ec2.connect_to_region(config.get('region'))

    # Check to see if specified key pair already exists.
    # If we get an InvalidKeyPair.NotFound error back from EC2,
    # it means that it doesn't exist and we need to create it.
    key_name = config.get('key_name')
    logger = logging.getLogger(__name__)
    try:
        key = ec2.get_all_key_pairs(keynames=[key_name])[0]
    except ec2.ResponseError, e:
        if e.code == 'InvalidKeyPair.NotFound':
            output = 'Creating key pair: %s' % key_name
            print output
            logger.info(output)
            # Create an SSH key to use when logging into instances.
            key = ec2.create_key_pair(key_name)

            # AWS will store the public key but the private key is
            # generated and returned and needs to be stored locally.
            # The save method will also chmod the file to protect
            # your private key.
            key.save(static.KEY_DIR)
        else:
            raise

    # Check to see if specified security group already exists.
    # If we get an InvalidGroup.NotFound error back from EC2,
    # it means that it doesn't exist and we need to create it.
    try:
        group = ec2.get_all_security_groups(groupnames=[static.SECURITY_GROUP_NAME])[0]
    except ec2.ResponseError, e:
        if e.code == 'InvalidGroup.NotFound':
            output = 'Creating Security Group: %s' % static.SECURITY_GROUP_NAME
            print output
            logger.info(output)
            # Create a security group to control access to instance via SSH.
            group = ec2.create_security_group(static.SECURITY_GROUP_NAME,
                'A group that allows SSH and HTTP access')
        else:
            raise

    # Add a rule to the security group to authorize SSH traffic on the specified port.
    try:
        group.authorize('tcp', static.SSH_PORT, static.SSH_PORT, static.CIDR_ANYONE)
        group.authorize('tcp', static.HTTPD_PORT, static.HTTPD_PORT, static.CIDR_ANYONE)
    except ec2.ResponseError, e:
        if e.code == 'InvalidPermission.Duplicate':
            #print 'Security Group %s already authorized' % static.SECURITY_GROUP_NAME
            pass
        else:
            raise

    # Now start up the instance.  The run_instances method
    # has many, many parameters but these are all we need
    # for now.
    reservation = ec2.run_instances(config.get('ami'),
        key_name=key_name,
        security_groups=[static.SECURITY_GROUP_NAME],
        instance_type=config.get('instance_type'))

    # Find the actual Instance object inside the Reservation object
    # returned by EC2.
    instance = reservation.instances[0]

    # The instance has been launched but it's not yet up and
    # running.  Let's wait for it's state to change to 'running'.
    #print 'Launching AWS EC2 instance'
    while instance.state != 'running':
        time.sleep(5)
        instance.update()
    logger.info('Instance %s with DNS %s started' % (instance.id, instance.public_dns_name))

    #Enable CloudWatch monitoring
    instance.monitor()

    # Let's tag the instance with the specified label so we can
    # identify it later.
    #instance.add_tag(static.)

    cmd = None

    #SSH connection test
    if connect:
        time.sleep(CONNECTION_DELAY)
        key_path = os.path.join(os.path.expanduser(static.KEY_DIR), key_name+static.KEY_EXTENSION)
        login_user = config.get('login_user')
        cmd = boto.manage.cmdshell.sshclient_from_instance(instance, key_path, user_name=login_user)

    return instance, cmd


def app_predeployment(config):
    logger = logging.getLogger(__name__)
    #Update mod_wsgi configuration
    wsgi_conf_writer.write_conf(config)
    #Zip the job
    aws_utils.prepare_archives()
    logger.info('Job and remote configuration are prepared for deployment')


def app_postdeployment(config):
    job_archive_file = static.JOB_BASE_NAME+'.'+static.ARCHIVE_FORMAT
    config_archive_file = static.RC_BASE_NAME+'.'+static.ARCHIVE_FORMAT
    local_job_path = config.get_home_dir() + 'aws/' + job_archive_file
    local_config_path = config.get_home_dir() + 'aws/' + config_archive_file
    os.remove(local_job_path)
    os.remove(local_config_path)


def deploy_app_at_instance(config, instance):
    """Deploy an app to EC2 instance. Thread-safe.
       Before invoking the method, job and config archives are to be created.
    """
    logger = logging.getLogger(__name__)
    job_archive_file = static.JOB_BASE_NAME+'.'+static.ARCHIVE_FORMAT
    config_archive_file = static.RC_BASE_NAME+'.'+static.ARCHIVE_FORMAT
    key_path = os.path.join(os.path.expanduser(static.KEY_DIR), config.get('key_name') + static.KEY_EXTENSION)
    login_user = config.get('login_user')
    local_job_path = config.get_home_dir() + 'aws/' + job_archive_file
    remote_job_path = '/home/%s/.deploy/job/%s' % (login_user,job_archive_file)
    local_config_path = config.get_home_dir() + 'aws/' + config_archive_file
    remote_config_path = '/home/%s/.deploy/config/%s' % (login_user,config_archive_file)

    cmd = boto.manage.cmdshell.sshclient_from_instance(instance, key_path, user_name=login_user)
    aws_utils.run_command(cmd, commands.PRE_DEPLOYMENT)
    logger.info('(%s) Pre-deployment maintenance tasks completed' % instance.id)

    cmd.put_file(local_job_path,remote_job_path)
    cmd.put_file(local_config_path,remote_config_path)
    logger.info('Updating the server and deploying the application')
    aws_utils.run_pty(cmd, commands.DEPLOYMENT %(config_archive_file, login_user, login_user))
    logger.info('(%s) Deployment maintenance task completed.' % instance.id)
    logger.info('App deployed at instance %s. Public DNS: %s' %(instance.id, instance.public_dns_name))


def get_availability_zones():
    config = Config()
    ec2 = boto.ec2.connect_to_region(config.get('region'))
    return ec2.get_all_zones()


def get_running_instances(config):
    """Return a list of instances running at the environment"""
    instances_in_env = config.get('instances').split(',')
    ec2 = boto.ec2.connect_to_region(config.get('region'))
    reservations = ec2.get_all_instances(filters = {'instance-state-name':'running'})
    running_instances_in_env = list()

    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id in instances_in_env:
                running_instances_in_env.append(instance)

    return running_instances_in_env


def terminate_instances(instances_to_terminate):
    """Terminate the EC2 instances given their IDs"""
    config = Config()
    logger = logging.getLogger(__name__)

    # Create a connection to EC2 service (assuming credentials are in boto config)
    ec2 = boto.ec2.connect_to_region(config.get('region'))
    reservations = ec2.get_all_instances(filters = {'instance-state-name':'running'})

    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id in instances_to_terminate:
                instance.terminate()
                logger.info('AWS EC2 instance %s terminated' % instance.id)


#def apply_paranoid_security():
#    # Check to see if specified security group already exists.
#    # If we get an InvalidGroup.NotFound error back from EC2,
#    # it means that it doesn't exist and we need to create it.
#    try:
#        group = ec2.get_all_security_groups(groupnames=[static.SECURITY_GROUP_NAME])[0]
#    except ec2.ResponseError, e:
#        if e.code == 'InvalidGroup.NotFound':
#            output = 'Creating Security Group: %s' % static.SECURITY_GROUP_NAME
#            print output
#            logger.info(output)
#            # Create a security group to control access to instance via SSH.
#            group = ec2.create_security_group(static.SECURITY_GROUP_NAME,
#                'A group that allows SSH and HTTP access')
#        else:
#            raise
#
#    # Add a rule to the security group to authorize SSH traffic on the specified port.
#    try:
#        group.authorize('tcp', static.SSH_PORT, static.SSH_PORT, static.CIDR_ANYONE)
#        group.authorize('tcp', static.HTTPD_PORT, static.HTTPD_PORT, static.CIDR_ANYONE)
#    except ec2.ResponseError, e:
#        if e.code == 'InvalidPermission.Duplicate':
#            #print 'Security Group %s already authorized' % static.SECURITY_GROUP_NAME
#            pass
#        else:
#            raise


