import ConfigParser
import os

CONFIG_FILE = 'aws/aws.config'
DEFAULT_SECTION = 'default'

class Config:
    """Works with the environment configuration"""

    config = None
    env_id = None

    def __init__(self, env_id=None):
        """Read config file upon init"""
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(open(self.get_home_dir() + CONFIG_FILE))
        self.config.read([self.get_home_dir() + CONFIG_FILE])
        self.env_id = env_id


    def write(self):
        """Write config file"""
        with open(self.get_home_dir() + CONFIG_FILE, 'wb') as configfile:
            self.config.write(configfile)


    def get(self,option):
        """Read an option from env_id section of config file. If not found, read from default section"""
        if not self.env_id or not self.config.has_section(self.env_id):
            return self.config.get(DEFAULT_SECTION,option)

        if self.config.has_option(self.env_id, option):
            return self.config.get(self.env_id, option)
        else:
            return self.config.get(DEFAULT_SECTION, option)


    def get_list(self,option):
        value = self.get(option).split(',')
        if len(value) == 1 and len(value[0]) == 0:
            value = []
        return value


    def getint(self,option):
        return int(self.get(option))


    def set(self,option,value):
        if not self.env_id:
            self.config.set(DEFAULT_SECTION,option,value)
            self.write()
            return

        if not self.config.has_section(self.env_id):
            self.config.add_section(self.env_id)
        self.config.set(self.env_id,option,value)
        self.write()


    def set_list(self,option,list):
        value = ','.join(list)
        self.set(option,value)


    def has_section(self,section):
        return self.config.has_section(section)


    def has_option(self,option):
        if self.env_id:
            return self.config.has_option(self.env_id,option) or self.config.has_option(DEFAULT_SECTION,option)
        else:
            return self.config.has_option(DEFAULT_SECTION,option)


    def remove_section(self,section):
        self.config.remove_section(section)
        self.write()


    def get_home_dir(self):
        dir = os.path.expanduser(os.environ['IN4392_HOME'])
        if not dir:
            dir = '.'
        if not dir.endswith('/'):
            dir += '/'
        return dir