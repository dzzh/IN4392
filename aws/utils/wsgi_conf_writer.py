from utils.config import Config

WSGI_CONF_FILE = 'aws/remote_config/etc/httpd/conf.d/wsgi.conf'

def write_conf(config):
    with open(config.get_home_dir() + WSGI_CONF_FILE, 'w') as f:
        f.write(get_header())
        f.write(get_vhost(config))
        f.close()

def get_header():
    return  'LoadModule wsgi_module modules/mod_wsgi.so\n' \
            'WSGIPythonHome /usr \n' \
            'WSGISocketPrefix run/wsgi \n' \
            'WSGIRestrictEmbedded On \n\n'

def get_vhost(config):

    daemon_process =    '\tWSGIDaemonProcess wsgi processes=%s threads=%s display-name=%%{GROUP} \\\n' \
                        '\tpython-path=/opt/python/current/app:/usr/lib/python2.6/site-packages user=wsgi group=wsgi\\\n'\
                        '\thome=/opt/python/current/app\n\n'

    vhost = '<VirtualHost *:80> \n' \
            '\tAlias /static /opt/python/current/app/static/ \n\n' \
            '\t<Directory /opt/python/current/app/> \n' \
            '\t\tOrder allow,deny \n' \
            '\t\tAllow from all \n'\
            '\t</Directory> \n\n' \
            '\tWSGIScriptAlias / /opt/python/current/app/application.py \n\n'\
            '\t<Directory /opt/python/current/app/> \n'\
            '\t\tOrder allow,deny \n'\
            '\t\tAllow from all \n'\
            '\t</Directory> \n\n'

    vhost += daemon_process % (config.get('wsgi_processes'),config.get('wsgi_threads'))

    vhost += '\tWSGIProcessGroup wsgi \n' \
             '</VirtualHost>'

    return vhost


