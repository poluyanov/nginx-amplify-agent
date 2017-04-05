# -*- coding: utf-8 -*-
import re


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


PS_CMD = "ps xao pid,ppid,command | grep 'php-fpm[:]'"


_PS_REGEX = re.compile(r'\s*(?P<pid>\d+)\s+(?P<ppid>\d+)\s+(?P<cmd>.+)\s*')


def PS_PARSER(ps_line):
    # parse ps response line...examples::
    #    36     1 php-fpm: master process (/etc/php/7.0/fpm/php-fpm.conf)
    #    37    36 php-fpm: pool www
    #    38    36 php-fpm: pool www
    parsed = _PS_REGEX.match(ps_line)

    if not parsed:
        return None

    pid, ppid, cmd = int(parsed.group('pid')), int(parsed.group('ppid')), parsed.group('cmd')
    return pid, ppid, cmd


_PS_MASTER_REGEX = re.compile(r'.*\((?P<conf_path>.*)\).*')


def MASTER_PARSER(ps_maseter_cmd):
    # parse ps master cmd line...:
    #   php-fpm: master process (/etc/php/7.0/fpm/php-fpm.conf)
    parsed = _PS_MASTER_REGEX.match(ps_maseter_cmd)

    if not parsed:
        return None

    conf_path = parsed.group('conf_path')
    return conf_path
