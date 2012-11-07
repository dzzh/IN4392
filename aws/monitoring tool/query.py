import web
import json
import random
import os
import gviz_api
import datetime
import cw
import types

urls = (
  "", "query",
)


class query:
     def GET(self):
  
        description = [("Date","datetime"),("CPUUtilization","number")]
        data_table = gviz_api.DataTable(description)
   
        user_data = web.input()
        inst_id = user_data.inst_id
        env=user_data.env
        
        data=cw.get_graph_data(env,inst_id)
        
        if data:
                data_table.LoadData(data)
                web.header("Content-Type", "text/plain")
                return data_table.ToJSonResponse()
        else:
            data=[[]]
            print "Problems at the query stage - returning empty data set from query"
            data_table.LoadData(data)
            web.header("Content-Type", "text/plain")
            return data_table.ToJSonResponse()
    

app_query = web.application(urls, locals())

  