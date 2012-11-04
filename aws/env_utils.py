import argparse
import logging
import boto
from boto.ec2 import cloudwatch
from utils.config import Config
from utils import aws_utils,wsgi_conf_writer
from services import aws_ec2

#A set of utils needed mostly for early-phase testing

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Different AWS maintenance utilities.')
    parser.add_argument('operation', metavar='op', type=str, choices=['get_log','write_wsgi','get_metrics'],
        help='Call to utility')
    parser.add_argument('-i', '--id', type=str, help='Instance ID')
    parser.add_argument('-e', '--eid', type=int, help='Environment ID')
    return parser.parse_args()


def get_metrics():
    config = Config('200')
    instances = aws_ec2.get_running_instances(config)
    print instances
    cw = boto.ec2.cloudwatch.connect_to_region('eu-west-1')
    metrics = cw.list_metrics(dimensions={u'InstanceId': [u'i-a85dc9e3']})

    for instance in instances:
        for metric in metrics:
            if 'InstanceId' in metric.dimensions and instance.id in metric.dimensions['InstanceId']:
                print metric



if __name__ == '__main__':
    args = parse_args()
    config = Config()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(config.get_home_dir() + "utils.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if args.operation == 'get_log':
        if not args.id:
            print 'Need to specify instance ID to retrieve the log'
        else:
            print aws_utils.get_console_log(args.id)
    if args.operation == 'write_wsgi':
        wsgi_conf_writer.write_conf()
    if args.operation == 'get_metrics':
        get_metrics()

