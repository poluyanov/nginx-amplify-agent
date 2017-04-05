# -*- coding: utf-8 -*-
from hamcrest import *
import time

from test.unit.ext.phpfpm.base import PHPFPMTestCase

from amplify.agent.common.context import context

from amplify.ext.phpfpm.objects.master import PHPFPMObject
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


class PHPFPMMetricsCollectorTestCase(PHPFPMTestCase):
    """
    Test case for PHPFPMMetricsCollector
    """

    def setup_method(self, method):
        super(PHPFPMMetricsCollectorTestCase, self).setup_method(method)
        context._setup_object_tank()

        self.phpfpm_obj = PHPFPMObject(
            local_id=123,
            pid=2,
            cmd='php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
            conf_path='/etc/php5/fpm/php-fpm.conf',
            workers=[3, 4]
        )

        context.objects.register(self.phpfpm_obj)

    def teardown_method(self, method):
        context._setup_object_tank()
        super(PHPFPMMetricsCollectorTestCase, self).setup_method(method)

    def test_init(self):
        phpfpm_metrics_collector = PHPFPMMetricsCollector(
            object=self.phpfpm_obj,
            interval=self.phpfpm_obj.intervals['metrics']
        )
        assert_that(phpfpm_metrics_collector, not_none())
        assert_that(phpfpm_metrics_collector, is_(PHPFPMMetricsCollector))

    def test_collect(self):
        phpfpm_metrics_collector = PHPFPMMetricsCollector(
            object=self.phpfpm_obj,
            interval=self.phpfpm_obj.intervals['metrics']
        )
        assert_that(phpfpm_metrics_collector, not_none())

        counted_vars = {'php.fpm.queue.req': 0, 'php.fpm.slow_req': 0, 'php.fpm.conn.accepted': 3}
        counted_vars_2 = {'php.fpm.queue.req': 5, 'php.fpm.slow_req': 4, 'php.fpm.conn.accepted': 5}

        # make direct aggregate call like a child collector would
        phpfpm_metrics_collector.aggregate_counters(counted_vars=counted_vars, stamp=1)

        # collect (runs increment)
        phpfpm_metrics_collector.collect()
        time.sleep(0.1)

        # first collect should not have counters
        assert_that(self.phpfpm_obj.statsd.current, not_(has_item('counter')))

        # make a second call
        phpfpm_metrics_collector.aggregate_counters(counted_vars=counted_vars_2, stamp=2)

        phpfpm_metrics_collector.collect()
        time.sleep(0.1)

        # now there should be counters
        assert_that(self.phpfpm_obj.statsd.current, has_item('counter'))

        counters = self.phpfpm_obj.statsd.current['counter']
        assert_that(counters, has_length(3))
        """
        counters:
        {
            'php.fpm.queue.req': [[2, 5]],
            'php.fpm.slow_req': [[2, 4]],
            'php.fpm.conn.accepted': [[2, 2]]
        }
        """
        assert_that(counters['php.fpm.queue.req'][0][1], equal_to(5))
        assert_that(counters['php.fpm.slow_req'][0][1], equal_to(4))
        assert_that(counters['php.fpm.conn.accepted'][0][1], equal_to(2))

        for metric_records in counters.itervalues():
            stamp = metric_records[0][0]   # get stamp from first recording in records
            assert_that(stamp, equal_to(2))
