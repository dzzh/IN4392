#The script is based on the Building Python Daemon Process article at
#http://www.gavinj.net/2012/06/building-python-daemon-process.html

#
# NOT WORKING YET
#

#standard python libs
import logging
import time

#third party libs
from daemon import runner
from utils.config import Config

class App():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path =  '/var/run/awsdaemon/awsdaemon.pid'
        self.pidfile_timeout = 5

    def run(self):
        while True:
            #Main code goes here ...
            #Note that logger level needs to be set to logging.DEBUG before this shows up in the logs
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warn("Warning message")
            logger.error("Error message")
            time.sleep(10)

app = App()
logger = logging.getLogger("AwsDaemon")
logger.setLevel(logging.INFO)
config = Config()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler(config.get_home_dir() + "monitor.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(app)
#This ensures that the logger file handle does not get closed during daemonization
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
