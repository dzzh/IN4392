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

JOB_ROOT_DIR   = '../job'
JOB_BASE_NAME  = 'job'

RC_ROOT_DIR    = 'remote_config'
RC_BASE_NAME   = 'config'
