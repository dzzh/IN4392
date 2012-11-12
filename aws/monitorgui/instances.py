from monitorgui import web
from utils import Config
from services import aws_ec2

urls = (
  "", "instances",
)

render = web.template.render('monitorgui/templates/')

class instances:
    def GET(self):
  
        user_data = web.input()
        env_id = user_data.env_id
        config = Config.Config (str(env_id))
                 
        #get stopped instances
        stopped_instances = list()
        stopped_instances=config.get_list('stopped_instances')
           
            
        #get running instances
        instance_list = aws_ec2.get_running_instances(config)
        instance_id_list = list()
        for instance in instance_list:
                instance_id_list.append(instance.id)
        
       
        return render.instances(instance_id_list,str(env_id),stopped_instances)
                   
        
       
    

app_instances = web.application(urls, locals())
