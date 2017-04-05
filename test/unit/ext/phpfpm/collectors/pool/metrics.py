# -*- coding: utf-8 -*-
from hamcrest import *
import time

from test.unit.ext.phpfpm.base import PHPFPMTestCase

from amplify.agent.common.context import context

from amplify.ext.phpfpm.objects.master import PHPFPMObject
from amplify.ext.phpfpm.objects.pool import PHPFPMPoolObject
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


class PHPFPMPoolMetricsCollectorTestCase(PHPFPMTestCase):
    """
    Test case for PHPFPMPoolMetricsCollector.
    """

    def setup_method(self, method):
        super(PHPFPMPoolMetricsCollectorTestCase, self).setup_method(method)
        context._setup_object_tank()

        self.phpfpm_obj = PHPFPMObject(
            local_id=123,
            pid=2,
            cmd='php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
            conf_path='/etc/php5/fpm/php-fpm.conf',
            workers=[3, 4]
        )

        context.objects.register(self.phpfpm_obj)

        pool_data = {
            'status_path': '/status',
            'name': 'www',
            'file': '/etc/php5/fpm/pool.d/www.conf',
            'listen': '/run/php/php7.0-fpm.sock'
        }

        self.phpfpm_pool_obj = PHPFPMPoolObject(
            local_id=124,
            parent_local_id=123,
            **pool_data
        )

        context.objects.register(self.phpfpm_pool_obj, parent_obj=self.phpfpm_obj)

    def teardown_method(self, method):
        context._setup_object_tank()
        super(PHPFPMPoolMetricsCollectorTestCase, self).setup_method(method)

    def test_init(self):
        phpfpm_pool_metrics_collector = PHPFPMPoolMetricsCollector(
            object=self.phpfpm_pool_obj,
            interval=self.phpfpm_pool_obj.intervals['metrics']
        )
        assert_that(phpfpm_pool_metrics_collector, not_none())
        assert_that(phpfpm_pool_metrics_collector, is_(PHPFPMPoolMetricsCollector))

    def test_collect(self):
        phpfpm_pool_metrics_collector = PHPFPMPoolMetricsCollector(
            object=self.phpfpm_pool_obj,
            interval=self.phpfpm_pool_obj.intervals['metrics']
        )
        assert_that(phpfpm_pool_metrics_collector, not_none())
        assert_that(self.phpfpm_pool_obj.statsd.current, equal_to({}))  # check that current is empty for obj.statsd

        # run collect
        phpfpm_pool_metrics_collector.collect()

        time.sleep(0.1)

        # run collect a second time for counters
        phpfpm_pool_metrics_collector.collect()

        # check that current is not empty
        assert_that(self.phpfpm_pool_obj.statsd.current, not_(equal_to({})))
        """
        statsd.current::

        {
            'counter': {
                'php.fpm.queue.req': [[1481301159.456794, 0]],
                'php.fpm.slow_req': [[1481301159.456794, 0]],
                'php.fpm.conn.accepted': [[1481301159.456794, 1]]
            },
            'gauge': {
                'php.fpm.proc.max_active': [(1481301159.355574, '1'), (1481301159.456794, '1')],
                'php.fpm.proc.max_child': [(1481301159.355574, '0'), (1481301159.456794, '0')],
                'php.fpm.queue.len': [(1481301159.355574, '0'), (1481301159.456794, '0')],
                'php.fpm.queue.max': [(1481301159.355574, '0'), (1481301159.456794, '0')],
                'php.fpm.proc.idle': [(1481301159.355574, '1'), (1481301159.456794, '1')],
                'php.fpm.proc.total': [(1481301159.355574, '2'), (1481301159.456794, '2')],
                'php.fpm.proc.active': [(1481301159.355574, '1'), (1481301159.456794, '1')],
            }
        }
        """
        counters = self.phpfpm_pool_obj.statsd.current['counter']
        assert_that(counters, has_length(3))

        gauges = self.phpfpm_pool_obj.statsd.current['gauge']
        assert_that(gauges, has_length(7))

        # run parent collect and check that child inserted metrics appropriately
        self.phpfpm_obj.collectors[1].collect()

        time.sleep(0.1)

        # need to run a second collect cycle for counters to populate in parent
        phpfpm_pool_metrics_collector.collect()

        time.sleep(0.1)

        self.phpfpm_obj.collectors[1].collect()

        time.sleep(0.1)

        # check parent to see also not empty
        assert_that(self.phpfpm_obj.statsd.current, not_(equal_to({})))
        counters = self.phpfpm_obj.statsd.current['counter']
        assert_that(counters, has_length(3))

        gauges = self.phpfpm_obj.statsd.current['gauge']
        assert_that(gauges, has_length(7))
