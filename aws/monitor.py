import argparse
from services import aws_ec2
from utils.config import Config

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Monitors the state of AWS environment and does autoscaling.')
    parser.add_argument('-e', '--eid', type=int, default=0, help='Environment ID')
    return parser.parse_args()


def validate_args(args, config):
    if not args.eid:
        print 'You should specify environment id to delete it'
        exit(1)

    if not config.has_section(str(args.eid)):
        print 'The environment with the specified id does not exist'
        exit(1)

    if args.eid and (args.eid < 100 or args.eid > 999):
        print 'ID should be in range [100,1000)'
        exit(1)

if __name__ == '__main__':
    config = Config()
    args = parse_args()
    validate_args(args,config)
    config.env_id = str(args.eid)

    running_instances = aws_ec2.get_running_instances(config.env_id)
