# -*- coding: utf-8 -*-
from amplify.ext.abstract.object import AbstractObject
from amplify.ext.phpfpm.util.parser import PHPFPMConfig
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

        self.name = 'master'

        # cached values
        self._local_id = self.data.get('local_id', None)
        # TODO: Think of a better way to handle this communication between asbtract and inherited objects.

        # attributes
        self.pid = self.data['pid']
        self.cmd = self.data['cmd']
        self.conf_path = self.data['conf_path']
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

        self.parsed_conf = PHPFPMConfig(path=self.conf_path).parsed
        self.parsed = True
        return self.parsed_conf
