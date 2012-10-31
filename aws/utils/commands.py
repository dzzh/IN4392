PRE_DEPLOYMENT = 'rm -rf .deploy/;' \
                 'mkdir -p ~/.deploy/config; ' \
                 'mkdir ~/.deploy/job; ' \
                 'mkdir ~/.deploy/scripts'

#You can add 'sudo yum -y update' before installing Apache, but it takes around 5 mins.
DEPLOYMENT     = 'cd .deploy/config; '\
                 'unzip %s; ' \
                 'rm config.zip; ' \
                 'sudo yum -y install httpd httpd-devel; ' \
                 'sudo yum -y install mod_wsgi; ' \
                 'sudo rm -rf /etc/httpd/conf; ' \
                 'sudo rm -rf /etc/httpd/conf.d; ' \
                 'sudo mkdir -p /opt/python/current/app; ' \
                 'sudo unzip -q /home/%s/.deploy/job/job.zip -d /opt/python/current/app; ' \
                 'sudo cp -r /home/%s/.deploy/config/* /; ' \
                 'sudo adduser wsgi; ' \
                 'sudo chmod 0777 /etc/httpd/run; ' \
                 'sudo /sbin/service httpd start'

