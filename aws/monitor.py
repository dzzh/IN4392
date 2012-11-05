import argparse
import logging
import time
from services import aws_cw, scale
from utils.config import Config

AUTOSCALE_CPU_PERCENTAGE_UP = 90
AUTOSCALE_CPU_PERCENTAGE_DOWN = 30

DELAY = 60 #Delay between retrieving new metrics in seconds

def parse_args():
    """Parse command-line args"""
    parser = argparse.ArgumentParser(
        description='Monitors the state of AWS environment and does autoscaling.')
    parser.add_argument('-e', '--eid', type=int, default=0, help='Environment ID')
    parser.add_argument('-n','--noscale',action='store_true',help='Prevent autoscaling.')
    return parser.parse_args()


def validate_args(args, config):
    """Validate correctness of command-line args"""
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

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO, filename=config.get_home_dir() + 'monitor.log')
    logger = logging.getLogger(__name__)

    while True:

        avg_cpu = aws_cw.get_avg_cpu_utilization_percentage_for_environment(config)
        logger.info('Current CPU utilization for the environment %s is %.2f percent'
                        % (config.env_id, avg_cpu))

        if avg_cpu > AUTOSCALE_CPU_PERCENTAGE_UP:
            if not args.noscale:
                if scale.scaling_up_possible(config):
                    scale.scale_up(config)
                else:
                    logger.warning('The environment has exceeded scaling capacity but further scaling needed.')
            else:
                logger.warning('The environment is highly loaded, scaling needed.')

        elif avg_cpu < AUTOSCALE_CPU_PERCENTAGE_DOWN:
            if not args.noscale:
                if scale.scaling_down_possible(config):
                    scale.scale_down(config)
            else:
                if scale.scaling_down_possible(config):
                    logger.info('The load on the environment is low, downscaling is possible.')

        time.sleep(DELAY)