############################################################
# Dockerfile to build Nginx Amplify Agent autotests
# Based on Gentoo
############################################################

# Set the base image to Ubuntu
FROM tianon/gentoo-stage3

# File Author / Maintainer
MAINTAINER Mike Belov

# Install basic applications
RUN emerge-webrsync
RUN emerge app-arch/tar net-misc/curl net-misc/wget nano dialog sys-apps/net-tools
RUN rm -rf /run && mkdir /run

# Install Python and Basic Python Tools
ADD make.conf /etc/portage/make.conf
RUN emerge python:2.7
RUN eselect python set python2.7

RUN emerge python-daemon
RUN python -m ensurepip
RUN pip install -U pip

# Install nginx
RUN emerge -1 portage
RUN emerge nginx

# Copy the application folder inside the container
ADD . /amplify

# Get pip to download and install requirements:
RUN pip install rstr==2.2.3 greenlet==0.4.9 gevent==1.0.2 lockfile==0.11.0 netaddr==0.7.18 netifaces==0.10.4 psutil==4.0.0 requests==2.10.0 ujson==1.33 python-daemon==2.0.6 pyparsing==2.0.1 setproctitle==1.1.10

ENV AMPLIFY_ENVIRONMENT development
ENV PYTHONPATH /amplify/

# Set the default directory where CMD will execute
WORKDIR /amplify

# add config
ADD nginx.conf /etc/nginx/nginx.conf

# add ssl
ADD amplify-agent-test.crt /etc/nginx/certs.d/amplify-agent-test.crt
ADD amplify-agent-test.key /etc/nginx/certs.d/amplify-agent-test.key

CMD /usr/sbin/nginx && python /amplify/nginx-amplify-agent.py start --config=/amplify/etc/agent.conf.development && tail -f /amplify/log/agent.log
