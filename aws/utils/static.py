#Security configuration
SECURITY_GROUP_NAME = "python"
KEY_DIR             = "~/.ssh/"
KEY_EXTENSION       = ".pem"

#Network configuration
SSH_PORT    = 22
HTTPD_PORT  = 80
CIDR_ANYONE = "0.0.0.0/0"

#Managing application and remote config to be deployed
ARCHIVE_FORMAT = 'zip'

JOB_ROOT_DIR   = 'job'
JOB_BASE_NAME  = 'job'

RC_ROOT_DIR    = 'aws/remote_config'
RC_BASE_NAME   = 'config'

#Autoscaling
AUTOSCALE_CPU_PERCENTAGE_UP = 80
AUTOSCALE_CPU_PERCENTAGE_DOWN = 30
AUTOSCALE_DELAY_AFTER_START = 30 #Delay between starting the instance and connecting to it, sec

#Monitoring
MONITOR_SLEEP_TIME = 60 #Delay between retrieving new metrics, sec
HEALTH_CHECKS = 3 #Number of health checks after which the instance is considered unhealthy if they fail consequently

#Instance launching
LAUNCH_CONNECTION_DELAY = 60 #empirically determined value which is sufficient for the instance
                             #to get ready for accepting ssh connection from a cold start, sec

