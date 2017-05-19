############################################################
# Dockerfile to build Nginx Amplify Agent container
# Based on Ubuntu 16.04
############################################################

# Set the base image to Ubuntu
FROM ubuntu:16.04

# File Author / Maintainer
MAINTAINER Mike Belov

# Add the application resources URL
# RUN echo "deb http://archive.ubuntu.com/ubuntu/ $(lsb_release -sc) main universe" >> /etc/apt/sources.list

# Update the sources list
RUN apt-get update

# Install basic applications
RUN apt-get install -y tar curl nano wget dialog net-tools build-essential
RUN apt-get install -y --fix-missing nginx

# Install php-fpm and configure
RUN apt-get update
RUN apt-get install -y php-fpm
# add fastcgi_params and php-fpm.conf for nginx
ADD fastcgi_params /etc/nginx/fastcgi_params
ADD php-fpm.conf /etc/nginx/conf.d/php-fpm.conf
# overwrite default www.conf for php7.0-fpm
ADD php-fpm-www.conf /etc/php/7.0/fpm/pool.d/www.conf
# add alternate version that listens on IPv4
ADD php-fpm-www-alt.conf /etc/php/7.0/fpm/pool.d/www-alt.conf
# add test .php file to /var/www/php-fpm root
ADD test.php /var/www/php-fpm/test.php

# Install Python and Basic Python Tools
RUN apt-get install -y python python-dev python-distribute
RUN wget --no-check-certificate https://bootstrap.pypa.io/ez_setup.py -O - | python
RUN easy_install pip

# Copy the application folder inside the container
ADD . /amplify

# Get pip to download and install requirements:
RUN pip install rstr==2.2.3 greenlet==0.4.9 gevent==1.0.2 lockfile==0.11.0 netaddr==0.7.18 netifaces==0.10.4 psutil==4.0.0 requests==2.12.4 ujson==1.33 python-daemon==2.0.6 pyparsing==2.0.1 setproctitle==1.1.10 flup==1.0.2

ENV AMPLIFY_ENVIRONMENT development
ENV PYTHONPATH /amplify/

# Set the default directory where CMD will execute
WORKDIR /amplify

# add stub status
ADD nginx.conf /etc/nginx/nginx.conf
ADD nginx2.conf /etc/nginx/nginx2.conf

# add ssl
ADD amplify-agent-test.crt /etc/nginx/certs.d/amplify-agent-test.crt
ADD amplify-agent-test.key /etc/nginx/certs.d/amplify-agent-test.key

CMD nginx && nginx -c /etc/nginx/nginx2.conf && service php7.0-fpm start && python /amplify/nginx-amplify-agent.py start --config=/amplify/etc/agent.conf.development && tail -f /amplify/log/agent.log