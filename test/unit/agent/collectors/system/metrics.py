# -*- coding: utf-8 -*-
import netifaces

import psutil
from hamcrest import *

from amplify.agent.collectors.system.metrics import SystemMetricsCollector
from amplify.agent.managers.system import SystemManager
from test.base import BaseTestCase, container_test
from test.helpers import collected_metric

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SystemMetricsCollectorTestCase(BaseTestCase):

    def get_collector(self, collect=True):
        manager = SystemManager()
        manager._discover_objects()
        obj = manager.objects.find_all(types=manager.types)[0]
        collector = SystemMetricsCollector(object=obj)
        if collect:
            collector.collect()
            collector.collect()  # second collect is needed to properly collect all metrics
        return collector

    def test_collect(self):
        collector = self.get_collector()
        metrics = collector.object.statsd.current

        # check counters
        assert_that(metrics, has_key('counter'))
        for counter in (
            'system.net.bytes_rcvd',
            'system.net.bytes_sent',
            'system.net.drops_in.count',
            'system.net.drops_out.count',
            'system.net.listen_overflows',
            'system.net.packets_in.count',
            'system.net.packets_in.error',
            'system.net.packets_out.count',
            'system.net.packets_out.error',
            starts_with('system.io.iops_r|'),
            starts_with('system.io.iops_w|'),
            starts_with('system.io.kbs_r|'),
            starts_with('system.io.kbs_w|'),
            starts_with('system.net.bytes_rcvd|'),
            starts_with('system.net.bytes_sent|'),
            starts_with('system.net.drops_in.count|'),
            starts_with('system.net.drops_out.count|'),
            starts_with('system.net.packets_in.count|'),
            starts_with('system.net.packets_in.error|'),
            starts_with('system.net.packets_out.count|'),
            starts_with('system.net.packets_out.error|')
        ):
            assert_that(metrics['counter'], has_entry(counter, collected_metric()))

        # check gauges
        assert_that(metrics, has_key('gauge'))
        for gauge in (
            'amplify.agent.cpu.system',
            'amplify.agent.cpu.user',
            'amplify.agent.mem.rss',
            'amplify.agent.mem.vms',
            'amplify.agent.status',
            'system.cpu.idle',
            'system.cpu.iowait',
            'system.cpu.stolen',
            'system.cpu.system',
            'system.cpu.user',
            'system.disk.free',
            'system.disk.in_use',
            'system.disk.total',
            'system.disk.used',
            'system.load.1',
            'system.load.15',
            'system.load.5',
            'system.mem.available',
            'system.mem.buffered',
            'system.mem.cached',
            'system.mem.free',
            'system.mem.pct_used',
            'system.mem.total',
            'system.mem.used',
            'system.swap.free',
            'system.swap.pct_free',
            'system.swap.total',
            'system.swap.used',
            starts_with('system.disk.total|'),
            starts_with('system.disk.used|'),
            starts_with('system.disk.free|'),
            starts_with('system.disk.in_use|'),
            starts_with('system.io.wait_r|'),
            starts_with('system.io.wait_w|')
        ):
            assert_that(metrics['gauge'], has_entry(gauge, collected_metric()))

    def test_agent_memory_info(self):
        collector = self.get_collector()
        metrics = collector.object.statsd.current
        assert_that(metrics, has_key('gauge'))
        assert_that(metrics['gauge'], has_entries('amplify.agent.mem.rss', collected_metric(greater_than(0))))
        assert_that(metrics['gauge'], has_entries('amplify.agent.mem.vms', collected_metric(greater_than(0))))

    def test_collect_only_alive_interfaces(self):
        collector = self.get_collector()

        # get interfaces info
        all_interfaces = netifaces.interfaces()
        alive_interfaces = set(name for name, iface in psutil.net_if_stats().iteritems() if iface.isup)

        # check
        collected_metrics = collector.object.statsd.current
        net_metrics_found = False
        for metric in collected_metrics['counter'].keys():
            if metric.startswith('system.net.') and '|' in metric:
                net_metrics_found = True
                metric_name, label_name = metric.split('|')
                assert_that(all_interfaces, has_item(label_name))
                assert_that(alive_interfaces, has_item(label_name))
        assert_that(net_metrics_found, equal_to(True))

    # This test doesn't really belong here...but it was the only test file that had a usable statsd object.
    def test_flush_aggregation(self):
        collector = self.get_collector()
        flush = collector.object.statsd.flush()
        for type in flush['metrics']:  # e.g. 'timer', 'counter', 'gauge', 'average'
            for key in flush['metrics'][type]:
                # Make sure there is only one item per item in the flush.
                assert_that(flush['metrics'][type][key], has_length(1))


@container_test
class SystemMetricsCollectorContainerTestCase(SystemMetricsCollectorTestCase):
    pass
