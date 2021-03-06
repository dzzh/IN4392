import distutils.archive_util
import logging
import boto.ec2
import datetime
import sys
from utils import static
from utils.config import Config

def get_console_log(instance_id):
    """Print console log of a given EC2 instance"""
    config = Config()
    ec2 = boto.ec2.connect_to_region(config.get('region'))
    reservations = ec2.get_all_instances(filters = {'instance-id':instance_id})
    if reservations:
        instance = reservations[0].instances[0]
        return instance.get_console_output().output
    else:
        return 'Instance with id %s not found' % instance_id


def prepare_archives():
    config = Config()
    dir_to_save = config.get_home_dir() + 'aws/'
    dir_to_archive = config.get_home_dir() + static.JOB_ROOT_DIR
    distutils.archive_util.make_archive(
        dir_to_save + static.JOB_BASE_NAME, static.ARCHIVE_FORMAT, root_dir=dir_to_archive)
    dir_to_archive = config.get_home_dir() + static.RC_ROOT_DIR
    distutils.archive_util.make_archive(
        dir_to_save + static.RC_BASE_NAME, static.ARCHIVE_FORMAT, root_dir=dir_to_archive)


def run_command(cmd, command):
    """Run remote command as a login-user"""
    logger = logging.getLogger(__name__)
    _, stdout, stderr = cmd.run(command)
    if stderr:
        print 'Command %s failed.' %command
        print 'Stderr contents:'
        print stderr
        logger.error('Command %s failed. Stderr contents:')
        logger.error(stderr)

def run_pty(cmd, command):
    """Run remote command as root"""
    logger = logging.getLogger(__name__)
    channel = cmd.run_pty(command)
    stderr = ''

    data = channel.recv_stderr(1024)
    while data:
        stderr += data
        data = channel.recv_stderr(1024)

    if stderr:
        print 'Command %s failed' %command
        print 'Stderr contents:'
        print stderr
        logger.error('Command %s failed. Stderr contents:')
        logger.error(stderr)


def apply_time_difference(time):
    """Takes time difference from config file and adjusts the supplied time in accordance with it"""
    config = Config()
    time_diff = int(config.get('time_difference'))
    delta = datetime.timedelta(hours=abs(time_diff))
    if time_diff < 0:
        return time - delta
    else:
        return time + delta





