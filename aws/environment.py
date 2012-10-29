import argparse
import random
from services import aws_ec2
from utils import aws_utils

def parse_args():
    """Parse command-line args"""

    parser = argparse.ArgumentParser(
        description='Performs operations with AWS environments.')

    parser.add_argument('operation', metavar='op', type=str, choices=['create', 'delete'],
        help='Operation on environment, either create or delete')
    parser.add_argument('-i', '--id', type=int, default=0, help='Environment ID')

    return parser.parse_args()

def validate_args(args, config):
    """Validate command-line args"""

    if args.operation == 'delete':
        if args.id == 0:
            print 'You should specify environment id to delete it'
            exit(1)

        if config.has_section(str(args.id)) == False:
            print 'The environment with the specified id does not exist'
            exit(1)

    if args.operation == 'create':
        if config.has_section(str(args.id)):
            print 'The environment with the specified id already exists'
            exit(1)

    if args.id != 0 and (args.id < 100 or args.id > 999):
        print 'ID should be in range [100,1000)'
        exit(1)

def create_environment(env_id, config):
    if env_id == '0':
        while env_id == '0' or config.has_section(env_id):
            env_id = str(random.randrange(100,1000))

    config.add_section(env_id)
    launch = aws_ec2.launch_instance()
    config.set(env_id,'instances',launch[0].id)
    print 'Created environment with id %s' % env_id
    return config

def delete_environment(env_id, config):

    instances = config.get(env_id,'instances').split(',')
    aws_ec2.terminate_instances(instances)

    #config.remove_section(env_id)
    return config

if __name__ == '__main__':

    config = aws_utils.read_config()

    args = parse_args()
    validate_args(args, config)

    env_id = str(args.id)
    if args.operation == 'create':
        config = create_environment(env_id, config)

    if args.operation == 'delete':
        config = delete_environment(env_id, config)

    aws_utils.write_config(config)

