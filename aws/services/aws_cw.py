import logging
import boto
from boto.ec2 import cloudwatch
import datetime
from services import aws_ec2
from utils import aws_utils

def get_avg_cpu_utilization_percentage_for_environment(config):
    """Return average CPU utilization for the given environment within some minutes specified in config"""
    logger = logging.getLogger(__name__)
    instances = aws_ec2.get_running_instances(config)
    cw = boto.ec2.cloudwatch.connect_to_region(config.get('region'))
    metrics = list()
    for instance in instances:
        list_metrics = cw.list_metrics(dimensions={'InstanceId': instance.id}, metric_name='CPUUtilization')
        #Newly added instances do not have recorded data, thus the query returns an empty list
        if len(list_metrics) > 0:
            metrics.append(list_metrics[0])

    dataset = list()
    for metric in metrics:
        end = aws_utils.apply_time_difference(datetime.datetime.now())
        delta = datetime.timedelta(seconds = end.second, microseconds = end.microsecond)
        end -= delta
        duration = datetime.timedelta(minutes=int(config.get('monitoring_period_minutes')), seconds=5)
        start = end - duration
        dataset.append(metric.query(start, end, ['Average']))

    total_avg = 0
    total_num = 0
    for index,entry in enumerate(dataset):
        inst_avg = 0
        inst_num = 0
        for record in entry:
            if record['Unit'] != 'Percent':
                print 'Wrong dataset submitted'
                exit(1)
            print record
            total_avg += record['Average']
            total_num += 1
            inst_avg += record['Average']
            inst_num += 1
        if inst_num:
            logger.info('Average CPU utilization at computational instance %d of %d is %.2f percents' \
                % (index + 1, len(dataset), inst_avg/inst_num))
        print '-----------'
    print 'End records'
    if not total_num:
        return 0
    else:
        return total_avg / total_num

