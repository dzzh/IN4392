#Security configuration
SECURITY_GROUP_NAME = "python"
KEY_DIR             = "~/.ssh/"
KEY_EXTENSION       = ".pem"

#Network configuration
SSH_PORT    = 22
HTTPD_PORT  = 80
CIDR_ANYONE = "0.0.0.0/0"

#Managing application to be deployed
ROOT_DIR           = '../job'
JOB_BASE_NAME     = 'job'
ARCHIVE_FORMAT    = 'zip'