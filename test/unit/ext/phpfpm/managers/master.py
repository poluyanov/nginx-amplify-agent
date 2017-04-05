# -*- coding: utf-8 -*-
from hamcrest import *
import time

from test.unit.ext.phpfpm.base import PHPFPMTestCase

from amplify.agent.common.context import context

from amplify.ext.phpfpm.managers.master import PHPFPMManager


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMManagerTestCase(PHPFPMTestCase):
    """
    Test case for PHPFPMManager (master).
    """

    def setup_method(self, method):
        super(PHPFPMManagerTestCase, self).setup_method(method)
        context._setup_object_tank()

    def teardown_method(self, method):
        context._setup_object_tank()
        super(PHPFPMManagerTestCase, self).teardown_method(method)

    def test_find_all(self):
        phpfpm_manager = PHPFPMManager()
        assert_that(phpfpm_manager, not_none())

        found_masters = phpfpm_manager._find_all()
        assert_that(found_masters, not_none())
        assert_that(found_masters, has_length(1))

        found_master = found_masters[0]
        assert_that(found_master['cmd'], equal_to('php-fpm: master process (/etc/php5/fpm/php-fpm.conf)'))
        assert_that(found_master['conf_path'], equal_to('/etc/php5/fpm/php-fpm.conf'))
        assert_that(found_master['pid'], not_none())
        assert_that(found_master['local_id'], equal_to(
            'af230c9e0343ec22e88333783e89857a0f5129b0fd8e4cfe21e12b1ae35fb3b4'
        ))
        assert_that(found_master['workers'], has_length(2))

    def test_discover_objects(self):
        phpfpm_manager = PHPFPMManager()
        assert_that(phpfpm_manager, not_none())

        # check to make sure there are no masters
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(0))

        # find masters
        phpfpm_manager._discover_objects()

        # check to see that a master is found
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(1))

    def test_stop_objects(self):
        phpfpm_manager = PHPFPMManager()
        assert_that(phpfpm_manager, not_none())

        # check to make sure there are no masters
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(0))

        # find masters
        phpfpm_manager._discover_objects()

        # check to see that a master is found
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(1))

        # stop php-fpm
        self.stop_fpm()

        # re-discover
        phpfpm_manager._discover_objects()

        # check to make sure there are no masters
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(0))

    def test_restart_objects(self):
        phpfpm_manager = PHPFPMManager()
        assert_that(phpfpm_manager, not_none())

        # check to make sure there are no masters
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(0))

        # find masters
        phpfpm_manager._discover_objects()

        # check to see that a master is found
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(1))

        # store the master id
        old_master_id = current_masters[0].id

        # stop php-fpm
        self.stop_fpm()

        time.sleep(0.1)  # release gil

        # restart php-fpm
        self.start_fpm()

        time.sleep(0.1)  # release gil

        # re-discover
        phpfpm_manager._discover_objects()

        # check to make sure there are no masters
        current_masters = context.objects.find_all(types=phpfpm_manager.types)
        assert_that(current_masters, has_length(1))

        master_id = current_masters[0].id
        assert_that(master_id, not_(equal_to(old_master_id)))
