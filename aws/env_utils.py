import argparse
import logging
from utils.config import Config
from utils import aws_utils
from services import aws_ec2
from pprint import pprint

#A set of utils needed mostly for early-phase testing

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Different AWS maintenance utilities.')
    parser.add_argument('operation', metavar='op', type=str, choices=['get_log','test'],
        help='Call to utility')
    parser.add_argument('-i', '--id', type=str, help='Instance ID')
    parser.add_argument('-e', '--eid', type=int, help='Environment ID')
    return parser.parse_args()


def test():
    config = Config('100')
    instance_id = 'i-3029b47b'
    instance = aws_ec2.get_instance(config,instance_id)
    pprint(vars(instance))


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
    if args.operation == 'test':
        test()

