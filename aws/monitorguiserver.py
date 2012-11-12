from monitorgui import web,query,chart_request_handler,instances
from monitorgui.web import form
from services import aws_ec2
from utils import Config


render = web.template.render('monitorgui/templates/')

urls = ('/', 'server', "/query", query.app_query, '/chart_request_handler', chart_request_handler.app_chart_request_handler,
        '/instances', instances.app_instances)
app = web.application(urls, globals())



class server: 
    def GET(self): 
        config = Config.Config()
        list_envs = [env for env in config.get_all_sections() if env != 'default']
        return render.environments(list_envs)
               
                
if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()