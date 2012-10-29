CONFIG_FILE = "aws.config"

import ConfigParser

def read_config():
    config = ConfigParser.ConfigParser()
    config.readfp(open(CONFIG_FILE))
    config.read([CONFIG_FILE])
    return config

def write_config(config):
    with open(CONFIG_FILE, 'wb') as configfile:
        config.write(configfile)
