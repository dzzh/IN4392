#!/bin/sh

cd /etc/httpd/conf.d
if !(grep --quiet 'Alias /static /opt/python/current/app/static/' wsgi.conf)
    then
        sudo sed -i 's:Alias /static /opt/python/current/app/:Alias /static /opt/python/current/app/static/:' wsgi.conf
fi
echo Script done