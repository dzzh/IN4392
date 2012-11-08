import logging
import boto
from boto.ec2 import cloudwatch
import time
import datetime
from services import aws_ec2
from utils import aws_utils
from utils.cw_classes import EnvMetric, InstanceMetric


def get_start_end_statistics_time(config):
    end = aws_utils.apply_time_difference(datetime.datetime.now())
    delta = datetime.timedelta(seconds = end.second, microseconds = end.microsecond)
    end -= delta
    duration = datetime.timedelta(minutes=int(config.get('monitoring_period_minutes')), seconds=5)
    start = end - duration
    return start,end


def get_avg_cpu_utilization_percentage_for_environment(config):
    """Return average CPU utilization for the given environment within number of minutes specified in config"""
    logger = logging.getLogger(__name__)
    instances = aws_ec2.get_running_instances(config)
    cw = boto.ec2.cloudwatch.connect_to_region(config.get('region'))
    env_metric = EnvMetric()
    for instance in instances:
        list_metrics = cw.list_metrics(dimensions={'InstanceId': instance.id}, metric_name='CPUUtilization')
        #Newly added instances do not have recorded data, thus the query returns an empty list
        if len(list_metrics) > 0:
            inst_metric = InstanceMetric(instance,list_metrics[0])
            start,end = get_start_end_statistics_time(config)
            inst_metric.query = list_metrics[0].query(start, end, ['Average'])
            percent, num = inst_metric.average_percentage()
            rec = str(inst_metric.metric_records())
            logger.info('In. %s: CPU %.2f for %d min. (%s)' %(inst_metric.instance.id, percent, num,rec))
            env_metric.instance_metrics.append(inst_metric)
    now = str(time.time()).split('.')[0]
    now_human = str(datetime.datetime.now())
    percent, num = env_metric.get_average_percentage()
    data = '%s, %s, %.2f, %d, %d' %(now_human, now, percent, len(config.get_list('instances')), len(config.get_list('stopped_instances')))
    logger.info(data)
    print(data)
    return env_metric


