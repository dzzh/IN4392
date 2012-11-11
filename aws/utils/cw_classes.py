class EnvMetric:
    instance_metrics = []

    def __init__(self):
        self.instance_metrics = []


    def get_average_percentage(self):
        result = 0
        num = 0
        for metric in self.instance_metrics:
            if len(metric.metric_records()) > 0:
                percent, _ = metric.average_percentage()
                result += percent
                num += 1
        if not num:
            return 0,0
        else:
            return result / num, num


    def get_least_loaded_instance(self):
        min_load = 100
        instance = self.instance_metrics[-1].instance.id
        for inst_metric in self.instance_metrics:
            percent, _ = inst_metric.average_percentage()
            if percent < min_load:
                min_load = percent
                instance = inst_metric.instance.id
        return instance


class InstanceMetric:

    instance = None
    metric = None
    query = None

    def __init__(self, instance, metric):
        self.instance = instance
        self.metric = metric


    def average_percentage(self):
        avg = 0
        num = 0
        for record in self.query:
            if record['Unit'] != 'Percent':
                print 'Wrong dataset submitted'
                exit(1)
            avg += record['Average']
            num += 1
        if not num:
            return 0, 0
        else:
            return avg / num, num


    def metric_records(self):
        result = {}
        for record in self.query:
            if record['Unit'] != 'Percent':
                print 'Wrong dataset submitted'
                exit(1)
            result[record['Timestamp'].minute] = record['Average']
        return result
