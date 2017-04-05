# -*- coding: utf-8 -*-

from amplify.ext.abstract.object import AbstractObject

from amplify.ext.phpfpm.collectors.pool.meta import PHPFPMPoolMetaCollector
from amplify.ext.phpfpm.collectors.pool.metrics import PHPFPMPoolMetricsCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMPoolObject(AbstractObject):
    type = 'phpfpm_pool'

    def __init__(self, **kwargs):
        super(PHPFPMPoolObject, self).__init__(**kwargs)

        # cached values
        self._name = self.data['name']
        self._local_id = self.data.get('local_id')

        # attributes
        self.parent_local_id = self.data['parent_local_id']
        self.listen = self.data['listen']
        self.status_path = self.data['status_path']

        # collectors
        self._setup_meta_collector()
        self._setup_metrics_collector()

    @property
    def local_id_args(self):
        return self.parent_local_id, self.name

    def _setup_meta_collector(self):
        self.collectors.append(
            PHPFPMPoolMetaCollector(object=self, interval=self.intervals['meta'])
        )

    def _setup_metrics_collector(self):
        self.collectors.append(
            PHPFPMPoolMetricsCollector(object=self, interval=self.intervals['metrics'])
        )
