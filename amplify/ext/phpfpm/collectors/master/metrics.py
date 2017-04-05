# -*- coding: utf-8 -*-
from amplify.agent.collectors.abstract import AbstractMetricsCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMMetricsCollector(AbstractMetricsCollector):
    """
    Metrics collector.  Spawned per master.  Sits around to aggregate counters from pool and periodically call
    increment.
    """
    short_name = 'phpfpm_metrics'

    def __init__(self, **kwargs):
        super(PHPFPMMetricsCollector, self).__init__(**kwargs)

    def collect(self, *args, **kwargs):
        """Just increment any and all updates from combined pools"""
        try:
            self.increment_counters()
        except Exception as e:
            self.handle_exception(self.increment_counters, e)
