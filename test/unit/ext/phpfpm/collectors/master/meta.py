# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.ext.phpfpm.objects.master import PHPFPMObject
from amplify.ext.phpfpm.collectors.master.meta import PHPFPMMetaCollector


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMMetaCollectorTestCase(BaseTestCase):
    """
    Test case for PHPFPMMetaCollector (master).
    """

    def setup_method(self, method):
        super(PHPFPMMetaCollectorTestCase, self).setup_method(method)
        self.phpfpm_obj = PHPFPMObject(
            local_id=123,
            pid=2,
            cmd='php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
            conf_path='/etc/php5/fpm/php-fpm.conf',
            bin_path='/usr/sbin/php-fpm7.0',
            workers=[3, 4]
        )

    def test_init(self):
        phpfpm_meta_collector = PHPFPMMetaCollector(object=self.phpfpm_obj, interval=self.phpfpm_obj.intervals['meta'])
        assert_that(phpfpm_meta_collector, not_none())
        assert_that(phpfpm_meta_collector, is_(PHPFPMMetaCollector))

    def test_collect(self):
        phpfpm_meta_collector = PHPFPMMetaCollector(object=self.phpfpm_obj, interval=self.phpfpm_obj.intervals['meta'])
        assert_that(phpfpm_meta_collector, not_none())
        assert_that(phpfpm_meta_collector.meta, equal_to({}))  # make sure meta is empty

        # collect and assert that meta is not empty
        phpfpm_meta_collector.collect()

        # check value
        assert_that(phpfpm_meta_collector.meta, equal_to(
            {
                'name': 'master',
                'display_name': 'phpfpm master @ hostname.nginx',
                'local_id': 123,
                'type': 'phpfpm',
                'workers': 2,
                'cmd': 'php-fpm: master process (/etc/php5/fpm/php-fpm.conf)',
                'pid': 2,
                'conf_path': '/etc/php5/fpm/php-fpm.conf',
                'root_uuid': None,
                'bin_path': '/usr/sbin/php-fpm7.0',
                'version': '7.0'
            }
        ))

        # check that it matches the object metad
        assert_that(phpfpm_meta_collector.meta, equal_to(self.phpfpm_obj.metad.current))
