# -*- coding: utf-8 -*-
import netifaces

import psutil
from hamcrest import *

from amplify.agent.collectors.system.meta import SystemMetaCollector
from amplify.agent.common.util import subp
from amplify.agent.managers.system import SystemManager
from test.base import BaseTestCase, container_test

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class SystemMetaCollectorTestCase(BaseTestCase):

    def get_collector(self, collect=True):
        manager = SystemManager()
        manager._discover_objects()
        obj = manager.objects.find_all(types=manager.types)[0]
        collector = SystemMetaCollector(object=obj)
        if collect:
            collector.collect()
        return collector

    def check_in_container(self, collector):
        assert_that(collector, has_property('in_container', False))

    def check_meta_keys(self, meta):
        assert_that(meta, has_key('boot'))
        assert_that(meta, has_key('hostname'))
        assert_that(meta, has_key('ec2'))
        assert_that(meta, not_(has_key('imagename')))
        assert_that(meta, not_(has_key('container_type')))

    def check_interface(self, interface_info):
        assert_that(interface_info, contains_inanyorder('mac', 'name', 'ipv4', 'ipv6'))
        assert_that(interface_info['ipv4'], contains_inanyorder('prefixlen', 'netmask', 'address'))
        assert_that(interface_info['ipv6'], contains_inanyorder('prefixlen', 'netmask', 'address'))

    def test_special_parse_restrictions(self):
        collector = self.get_collector(collect=False)
        self.check_in_container(collector)
        collector.collect()
        meta = collector.object.metad.current
        self.check_meta_keys(meta)

    def test_tags(self):
        collector = self.get_collector()
        meta = collector.object.metad.current
        assert_that(meta, has_entries(
            tags=contains(
                has_entries(key=none(), value='foo'),
                has_entries(key=none(), value='bar'),
                has_entries(key='foo', value='bar')
            )
        ))

    def test_parse_only_alive_interfaces(self):
        collector = self.get_collector()
        meta = collector.object.metad.current

        # get interfaces info
        all_interfaces = netifaces.interfaces()
        alive_interfaces = set(name for name, iface in psutil.net_if_stats().iteritems() if iface.isup)

        # check interfaces
        for interface_info in meta['network']['interfaces']:
            self.check_interface(interface_info)
            assert_that(interface_info['name'], is_in(all_interfaces))
            assert_that(interface_info['name'], is_in(alive_interfaces))

    def test_default_interface(self):
        collector = self.get_collector()
        meta = collector.object.metad.current
        out, __ = subp.call('netstat -nr | egrep -i "^0.0.0.0|default" | head -1 | sed "s/.*[ ]\([^ ][^ ]*\)$/\\1/"')
        default_from_netstat = out[0]
        assert_that(meta['network']['default'], equal_to(default_from_netstat))

    def test_collect_each_interface_once(self):
        collector = self.get_collector(collect=False)
        num_interfaces = len(psutil.net_if_stats())
        for x in xrange(3):
            collector.collect()
            meta = collector.object.metad.current
            collected_interfaces = meta['network']['interfaces']
            assert_that(collected_interfaces, has_length(num_interfaces))
            for interface_info in collected_interfaces:
                self.check_interface(interface_info)


@container_test
class SystemMetaCollectorContainerTestCase(SystemMetaCollectorTestCase):

    def check_in_container(self, collector):
        assert_that(collector, has_property('in_container', True))

    def check_meta_keys(self, meta):
        assert_that(meta, not_(has_key('boot')))
        assert_that(meta, not_(has_key('hostname')))
        assert_that(meta, not_(has_key('ec2')))
        assert_that(meta, has_key('imagename'))
        assert_that(meta, has_key('container_type'))

    def check_interface(self, interface_info):
        assert_that(interface_info, contains_inanyorder('mac', 'name'))
