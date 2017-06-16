# -*- coding: utf-8 -*-
from hamcrest import (
    assert_that, not_none, is_, equal_to
)

from amplify.agent.common.context import context

from test.unit.ext.phpfpm.base import PHPFPMTestCase
from amplify.ext.phpfpm.managers.master import PHPFPMManager

from amplify.ext.phpfpm.collectors.master.meta import PHPFPMMetaCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov",
    "Andrew Alexeev", "Grant Hulegaard", "Arie van Luttikhuizen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMMetaCollectorTestCase(PHPFPMTestCase):
    """
    Test case for PHPFPMMetaCollector (master).
    """

    def setup_method(self, method):
        super(PHPFPMMetaCollectorTestCase, self).setup_method(method)
        context._setup_object_tank()

        phpfpm_manager = PHPFPMManager()
        phpfpm_manager._discover_objects()
        found_masters = context.objects.find_all(types=phpfpm_manager.types)

        self.phpfpm_obj = found_masters[0]

    def teardown_method(self, method):

        context._setup_object_tank()
        super(PHPFPMMetaCollectorTestCase, self).teardown_method(method)

    def test_init(self):
        phpfpm_meta_collector = PHPFPMMetaCollector(
            object=self.phpfpm_obj, interval=self.phpfpm_obj.intervals['meta']
        )
        assert_that(phpfpm_meta_collector, not_none())
        assert_that(phpfpm_meta_collector, is_(PHPFPMMetaCollector))

    def test_collect(self):
        phpfpm_meta_collector = PHPFPMMetaCollector(
            object=self.phpfpm_obj, interval=self.phpfpm_obj.intervals['meta']
        )
        assert_that(phpfpm_meta_collector, not_none())
        # make sure meta is empty
        assert_that(phpfpm_meta_collector.meta, equal_to({}))

        # collect and assert that meta is not empty
        phpfpm_meta_collector.collect()

        # collect twice in case bin_path found second
        phpfpm_meta_collector.collect()

        # check value
        assert_that(phpfpm_meta_collector.meta, equal_to(
            {
                'name': 'master',
                'display_name': 'phpfpm master @ hostname.nginx',
                'local_id': 'af230c9e0343ec22e88333783e89857a0f5129b0fd8e4cfe2'
                            '1e12b1ae35fb3b4',
                'type': 'phpfpm',
                'workers': 2,
                'cmd': 'php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
                'pid': self.phpfpm_obj.pid,
                'conf_path': '/etc/php5/fpm/php-fpm.conf',
                'root_uuid': None,
                'bin_path': '/usr/sbin/php5-fpm',
                'version': '5.5.9-1',
                'version_line': 'PHP 5.5.9-1ubuntu4.21 (fpm-fcgi) (built: Feb '
                                ' 9 2017 21:00:52)'
            }
        ))

        # check that it matches the object metad
        assert_that(
            phpfpm_meta_collector.meta,
            equal_to(self.phpfpm_obj.metad.current)
        )

    def test_collect_no_bin(self):
        """
        This test is supposed to test the resilience of the new bin_path
        collection.  This is tricky to test an actual situation, so what we are
        doing is stopping the running PHPFPM object before running collect.
        This is a poor analog for the situation we want to test, but it is what
        is possible from inside a container environment.
        """
        phpfpm_meta_collector = PHPFPMMetaCollector(
            object=self.phpfpm_obj, interval=self.phpfpm_obj.intervals['meta']
        )
        assert_that(phpfpm_meta_collector, not_none())
        # make sure meta is empty
        assert_that(phpfpm_meta_collector.meta, equal_to({}))

        # stop phpfpm so collector cannot actually hit the pid with ls...this
        # will be a different error than "permissions" but it will error all
        # the same
        self.stop_fpm()

        # collect and assert that meta is not empty
        phpfpm_meta_collector.collect()

        # check value
        assert_that(phpfpm_meta_collector.meta, equal_to(
            {
                'name': 'master',
                'display_name': 'phpfpm master @ hostname.nginx',
                'local_id': 'af230c9e0343ec22e88333783e89857a0f5129b0fd8e4cfe2'
                            '1e12b1ae35fb3b4',
                'type': 'phpfpm',
                'workers': 2,
                'cmd': 'php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
                'pid': self.phpfpm_obj.pid,
                'conf_path': '/etc/php5/fpm/php-fpm.conf',
                'root_uuid': None,
                'bin_path': None,
                'version': None,
                'version_line': None
            }
        ))

        # check that it matches the object metad
        assert_that(
            phpfpm_meta_collector.meta,
            equal_to(self.phpfpm_obj.metad.current)
        )
