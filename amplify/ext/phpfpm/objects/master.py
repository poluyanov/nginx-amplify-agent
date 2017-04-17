# -*- coding: utf-8 -*-
import ConfigParser
import glob

from amplify.agent.common.context import context
from amplify.ext.abstract.object import AbstractObject
from amplify.ext.phpfpm.collectors.master.meta import PHPFPMMetaCollector
from amplify.ext.phpfpm.collectors.master.metrics import PHPFPMMetricsCollector

__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMObject(AbstractObject):
    type = 'phpfpm'

    def __init__(self, **kwargs):
        super(PHPFPMObject, self).__init__(**kwargs)

        # cached values
        self._name = self.data['conf_path']
        self._local_id = self.data.get('local_id')

        # attributes
        self.pid = self.data['pid']
        self.cmd = self.data['cmd']
        self.conf_path = self._name
        self.workers = self.data['workers']

        # state
        self.parsed_conf = None
        self.parsed = False

        # collectors
        self._setup_meta_collector()
        self._setup_metrics_collector()

    @property
    def local_id_args(self):
        return self.cmd, self.conf_path

    def _setup_meta_collector(self):
        self.collectors.append(
            PHPFPMMetaCollector(object=self, interval=self.intervals['meta'])
        )

    def _setup_metrics_collector(self):
        self.collectors.append(
            PHPFPMMetricsCollector(object=self, interval=self.intervals['metrics'])
        )

    def parse(self, force=False):
        if self.parsed and not force:
            return self.parsed_conf

        parsed_results = {
            'file': self.conf_path,
            'include': [],
            'pools': []
        }

        # parse root config
        try:
            root_config = ConfigParser.ConfigParser()
            root_config.read(self.conf_path)

            parsed_results['include'].append(root_config.get('global', 'include'))

        except Exception as e:
            exception_name = e.__class__.__name__
            context.log.error('failed to parse php-fpm master config %s due to %s' % (self.conf_path, exception_name))
            context.log.debug('additional info:', exc_info=True)

        # find included configs (pools)
        included = []
        for include_rule in parsed_results['include']:
            if '*' in include_rule:
                for filepath in glob.glob(include_rule):
                    included.append(filepath)

        # parse included configs (pools)
        for filepath in included:
            pool = {
                'file': filepath,
                'name': None,
                'listen': None,
                'status_path': None
            }
            try:
                pool_config = ConfigParser.ConfigParser()
                pool_config.read(filepath)

                pool_name = pool_config.sections()[0]
                pool['name'] = pool_name

                listen = pool_config.get(pool_name, 'listen')
                pool['listen'] = listen

                status_path = pool_config.get(pool_name, 'pm.status_path')
                pool['status_path'] = status_path
            except Exception as e:
                exception_name = e.__class__.__name__
                context.log.error('failed to parse php-fpm pool config %s due to %s' % (filepath, exception_name))
                context.log.debug('additional info:', exc_info=True)
            else:
                # only add pool if there is no error and if pool is properly
                parsed_results['pools'].append(pool)

        self.parsed_conf = parsed_results
        self.parsed = True
        return self.parsed_conf
