#IN4392

##Overview

This project contains lab work for IN4392 Cloud Computing course at TU Delft. The aim of the project is to implement a resource manager for AWS cloud which should operate similarly to the Elastic Beanstalk service and simplify the deployment of web applications using Python and WSGI at AWS machines. 

##Prerequisites

To work with IN4392, the following should be done in advance.

* Somehow get UNIX-like OS. Windows sucks and I'm lazy, here are the two serious reasons not to support it.
* Install Python 2.6<=workingversion<3.
* Install [boto](https://github.com/boto/boto).
* Install [paramiko](http://www.lag.net/paramiko/).
* Add your ACCESS_KEY_ID and SECRET_ACCESS_KEY either to boto config file or set them as environment variables.
* Copy `in4392/aws/aws.config.default` to `in4392/aws/aws.config` and adjust the configuration in it as you wish.

##Installation

IN4392 does not require installation, but some procedures can be done with your profile file to simplify its usage.

* Add an alias to the main file, i.e. `alias awsenv="python /path/to/in4392/aws/environment.py"`
* Set `IN4392_HOME` variable and point it to in4392 folder.

##Workflow

IN4392 is already supplied with a sample WSGI Python application. If you want to use your application instead, you have to place it inside job/ folder. After you are done, you should proceed as follows.

* run `awsenv create` to create AWS environment. In the console output you will see the automatically generated environment ID to be used in further operations. You can specify your own ID with -e command-line argument. After creating the environment you will be provided with the DNS name of a load balancer that you would use to access the application.
* run `awsenv deploy -e <id>` to deploy your application to the environment. This procedure may take several minutes. After it is completed, you may point your browser to DNS obtained at a previous step to see it working at AWS platform. Sometimes the application may be inaccessible for several minutes after the deployment due to the need to establish proper communication between the load balancer and EC2 instances.
* run `awsenv delete -e <id>` to delete the environment.
