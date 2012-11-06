import web
from web import form
import query
import chart_request_handler
from services import aws_ec2
from utils.Config import Config

render = web.template.render('templates/')

urls = ('/', 'server', "/query", query.app_query, '/chart_request_handler', chart_request_handler.app_chart_request_handler)
app = web.application(urls, globals())

myform = form.Form( 
    form.Textbox("EnvironmentID")
   ) 

class server: 
    def GET(self): 
        form = myform()
        return render.the_form(form)

    def POST(self): 
        form = myform() 
        if not form.validates(): 
            return render.the_form(form)
        else:
            try:
                config = Config (str(form.d.EnvironmentID))
                instance_list = list()
                instance_list = aws_ec2.get_running_instances(config)
                instance_id_list = list()
                for instance in instance_list:
                    instance_id_list.append(instance.id)
                if instance_id_list:
                    return render.instances(instance_id_list,str(form.d.EnvironmentID))
                else:
                    return "There are no running instances at the moment."
            except:
                return "The requested environment ID is not found in the config file."

if __name__=="__main__":
    web.internalerror = web.debugerror
    app.run()