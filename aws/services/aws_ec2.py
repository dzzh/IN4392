import os
import time
import boto
import boto.ec2
import boto.manage.cmdshell

from utils import aws_utils, static

#The function is based on ec2_launch_instance.py from Python and AWS Cookbook
def launch_instance(connect):
    """Launch an instance and wait for it to start running.
    Returns a tuple consisting of the Instance object and the CmdShell object,
    if request, or None.

    -connect tells to perform the SSH connection test to the newly created instance (up to 1 min of time)
    """

    config = aws_utils.read_config()

    # Create a connection to EC2 service (assuming credentials are in boto config)
    ec2 = boto.ec2.connect_to_region(config.get('environment','region'))

    # Check to see if specified key pair already exists.
    # If we get an InvalidKeyPair.NotFound error back from EC2,
    # it means that it doesn't exist and we need to create it.
    key_name = config.get('environment','key_name')
    try:
        key = ec2.get_all_key_pairs(keynames=[key_name])[0]
    except ec2.ResponseError, e:
        if e.code == 'InvalidKeyPair.NotFound':
            print 'Creating keypair: %s' % key_name
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
            print 'Creating Security Group: %s' % static.SECURITY_GROUP_NAME
            # Create a security group to control access to instance via SSH.
            group = ec2.create_security_group(static.SECURITY_GROUP_NAME,
                'A group that allows SSH access')
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
    reservation = ec2.run_instances(config.get('environment','ami'),
        key_name=key_name,
        security_groups=[static.SECURITY_GROUP_NAME],
        instance_type=config.get('environment', 'instance_type'))

    # Find the actual Instance object inside the Reservation object
    # returned by EC2.
    instance = reservation.instances[0]

    # The instance has been launched but it's not yet up and
    # running.  Let's wait for it's state to change to 'running'.
    #print 'Launching AWS EC2 instance'
    while instance.state != 'running':
        time.sleep(5)
        instance.update()
    print 'Instance %s started' % instance.public_dns_name

    # Let's tag the instance with the specified label so we can
    # identify it later.
    #instance.add_tag(static.)

    cmd = None

    #SSH connection test
    if connect:
        #print 'Connecting to the newly created instance (may take up to 1 minute and sometimes even more)'
        time.sleep(45)  #empirically determined value which is sufficient for the instance
                        # to get ready for accepting ssh connection

        key_path = os.path.join(os.path.expanduser(static.KEY_DIR), key_name+static.KEY_EXTENSION)
        login_user = config.get('environment','login_user')
        cmd = boto.manage.cmdshell.sshclient_from_instance(instance, key_path, user_name=login_user)

    return instance, cmd


def get_running_instances(env_id):
    """Return a list of instances running at the environment"""
    config = aws_utils.read_config()
    instances_in_env = config.get(env_id,'instances').split()
    ec2 = boto.ec2.connect_to_region(config.get('environment','region'))
    reservations = ec2.get_all_instances(filters = {'instance-state-name':'running'})
    running_instances_in_env = list()

    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id in instances_in_env:
                running_instances_in_env.append(instance)

    return running_instances_in_env

def terminate_instances(instances_to_terminate):
    """Terminate the EC2 instances given their IDs"""
    config = aws_utils.read_config()

    # Create a connection to EC2 service (assuming credentials are in boto config)
    ec2 = boto.ec2.connect_to_region(config.get('environment','region'))
    reservations = ec2.get_all_instances(filters = {'instance-state-name':'running'})

    for reservation in reservations:
        for instance in reservation.instances:
            if instance.id in instances_to_terminate:
                instance.terminate()
                print 'AWS EC2 instance %s terminated' % instance.id

