import distutils.archive_util
import boto.ec2
from utils import static

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


def prepare_archives():
    distutils.archive_util.make_archive(
        static.JOB_BASE_NAME, static.ARCHIVE_FORMAT, root_dir=static.JOB_ROOT_DIR)
    distutils.archive_util.make_archive(
        static.RC_BASE_NAME, static.ARCHIVE_FORMAT, root_dir=static.RC_ROOT_DIR)


def run_command(cmd, command):
    """Run remote command as a login-user"""
    _, stdout, stderr = cmd.run(command)
    if stderr:
        print 'Stderr contents:'
        print stderr

def run_pty(cmd, command):
    """Run remote command as root"""
    channel = cmd.run_pty(command)
    stdout = ''
    stderr = ''

    data = channel.recv(1024)
    while data:
        stdout += data
        data = channel.recv(1024)

    data = channel.recv_stderr(1024)
    while data:
        stderr += data
        data = channel.recv_stderr(1024)

    if stderr:
        print 'Stderr contents:'
        print stderr

    print stdout



