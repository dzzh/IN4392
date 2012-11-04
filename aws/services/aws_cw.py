import boto
from boto.ec2 import cloudwatch
import datetime
from services import aws_ec2
from utils import aws_utils

def get_avg_cpu_utilization_percentage_for_environment(config):
    instances = aws_ec2.get_running_instances(config)

    cw = boto.ec2.cloudwatch.connect_to_region(config.get('region'))
    metrics = cw.list_metrics(dimensions={'InstanceId': [i.id for i in instances]}, metric_name='CPUUtilization')
    print [metric.dimensions for metric in metrics]
    dataset = list()
    for metric in metrics:
        end = aws_utils.apply_time_difference(datetime.datetime.now())
        delta = datetime.timedelta(seconds = end.second, microseconds = end.microsecond)
        end -= delta
        duration = datetime.timedelta(minutes=int(config.get('monitoring_period_minutes'))+1)
        start = end - duration
        dataset.append(metric.query(start, end, ['Average']))

    avg_sum = 0
    num = 0
    for entry in dataset:
        for record in entry:
            if record['Unit'] != 'Percent':
                print 'Wrong dataset submitted'
                exit(1)
            avg_sum += record['Average']
            num += 1
    if num == 0:
        return 0
    else:
        return avg_sum / num

