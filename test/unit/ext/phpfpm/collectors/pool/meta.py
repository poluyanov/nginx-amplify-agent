# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.ext.phpfpm.objects.pool import PHPFPMPoolObject
from amplify.ext.phpfpm.collectors.pool.meta import PHPFPMPoolMetaCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMPoolMetaCollectorTestCase(BaseTestCase):
    """
    Test case for PHPFPMPoolMetaCollector.
    """

    def setup_method(self, method):
        super(PHPFPMPoolMetaCollectorTestCase, self).setup_method(method)
        self.phpfpm_pool_obj = PHPFPMPoolObject(
            local_id=124,
            parent_local_id=123,
            status_path='/status',
            name='www',
            file='/etc/php5/fpm/pool.d/www.conf',
            listen='/run/php/php7.0-fpm.sock'
        )

    def test_init(self):
        phpfpm_pool_meta_collector = PHPFPMPoolMetaCollector(
            object=self.phpfpm_pool_obj,
            interval=self.phpfpm_pool_obj.intervals['meta']
        )
        assert_that(phpfpm_pool_meta_collector, not_none())
        assert_that(phpfpm_pool_meta_collector, is_(PHPFPMPoolMetaCollector))

    def test_collect(self):
        phpfpm_pool_meta_collector = PHPFPMPoolMetaCollector(
            object=self.phpfpm_pool_obj,
            interval=self.phpfpm_pool_obj.intervals['meta']
        )
        assert_that(phpfpm_pool_meta_collector, not_none())
        assert_that(phpfpm_pool_meta_collector.meta, equal_to({}))  # make sure meta is empty

        # collect and assert that meta is not empty
        phpfpm_pool_meta_collector.collect()

        # check value
        assert_that(phpfpm_pool_meta_collector.meta, equal_to(
            {
                'listen': '/run/php/php7.0-fpm.sock',
                'flisten': '/run/php/php7.0-fpm.sock',
                'local_id': 124,
                'name': 'www',
                'display_name': 'phpfpm www @ hostname.nginx',
                'parent_local_id': 123,
                'status_path': '/status',
                'type': 'phpfpm_pool',
                'root_uuid': None,
                'can_have_children': False
            }
        ))

        # check that it matches the object metad
        assert_that(phpfpm_pool_meta_collector.meta, equal_to(self.phpfpm_pool_obj.metad.current))

    def test_collect_flisten(self):
        phpfpm_pool_obj = PHPFPMPoolObject(
            local_id=124,
            parent_local_id=123,
            status_path='/status',
            name='www',
            file='/etc/php5/fpm/pool.d/www.conf',
            listen='/run/php/$pool.sock'
        )
        phpfpm_pool_meta_collector = PHPFPMPoolMetaCollector(
            object=phpfpm_pool_obj,
            interval=self.phpfpm_pool_obj.intervals['meta']
        )
        assert_that(phpfpm_pool_meta_collector, not_none())
        assert_that(phpfpm_pool_meta_collector.meta, equal_to({}))  # make sure meta is empty

        # collect and assert that meta is not empty
        phpfpm_pool_meta_collector.collect()

        # check value
        assert_that(phpfpm_pool_meta_collector.meta, equal_to(
            {
                'listen': '/run/php/$pool.sock',
                'flisten': '/run/php/www.sock',
                'local_id': 124,
                'name': 'www',
                'display_name': 'phpfpm www @ hostname.nginx',
                'parent_local_id': 123,
                'status_path': '/status',
                'type': 'phpfpm_pool',
                'root_uuid': None,
                'can_have_children': False
            }
        ))

        # check that it matches the object metad
        assert_that(phpfpm_pool_meta_collector.meta, equal_to(phpfpm_pool_obj.metad.current))
