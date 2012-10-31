import argparse
from utils import aws_utils

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Different AWS maintenance utilities.')
    parser.add_argument('operation', metavar='op', type=str, choices=['get_log'],
        help='Call to utility')
    parser.add_argument('-i', '--id', type=str, help='Instance ID')
    parser.add_argument('-e', '--eid', type=int, help='Environment ID')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    if args.operation == 'get_log':
        if not args.id:
            print 'Need to specify instance ID to retrieve the log'
        else:
            print aws_utils.get_console_log(args.id)

