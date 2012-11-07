from utils.config import Config
from services import aws_ec2
from boto import utils
import boto
import datetime
import boto.ec2.cloudwatch
import operator

def get_adjusted_period(nr_sec):

    #minimum period for CloudWatch to work.
    period=60
    while  nr_sec > 1440 * period :
          period+=60
    return period

def get_monitoring_information_from_start(config_id,instanceID,metric_q,statistic,unit):

    config = Config(config_id)
    cw = boto.ec2.cloudwatch.connect_to_region(config.get('region'))
    metrics = cw.list_metrics(dimensions={'InstanceId': instanceID}, 
                                     metric_name=metric_q)
    if metrics:
        inst = aws_ec2.get_instance(config, instanceID)
        end_time = datetime.datetime.utcnow()
        start_time=boto.utils.parse_ts(inst.launch_time)

        #get nr of seconds
        diff = end_time - start_time 
        seconds = diff.total_seconds()
    
        #adjust the period
        period=get_adjusted_period(seconds)
        result = metrics[0].query(start_time,end_time,statistic,unit,period)
        return sorted(result, key = operator.itemgetter(u'Timestamp'))

def get_graph_data(config_id,instance_id):
    result_list=list()
    l = get_monitoring_information_from_start(str(config_id),str(instance_id),"CPUUtilization","Average","Percent")
    for item in l:
        result_list.append([item.values()[0],item.values()[1]])
    return result_list

if __name__ == "__main__":
    main()
   