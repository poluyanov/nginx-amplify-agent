# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase, RealNginxTestCase

from amplify.agent.common.context import context
from amplify.agent.tanks.nginx_config import NginxConfigTank
from amplify.agent.managers.nginx import NginxManager
from amplify.agent.objects.nginx.config.config import NginxConfig


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard"]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class NginxConfigTankTestCase(BaseTestCase):
    def setup_method(self, method):
        super(NginxConfigTankTestCase, self).setup_method(method)

        context.nginx_configs = None
        self.nginx_configs = NginxConfigTank()

    def teardown_method(self, method):
        self.nginx_configs = None
        context.nginx_configs = NginxConfigTank()

        super(NginxConfigTankTestCase, self).teardown_method(method)

    def test_init(self):
        assert_that(self.nginx_configs, not_none())

    def test_len(self):
        assert_that(self.nginx_configs, has_length(0))

    def test_keys(self):
        assert_that(self.nginx_configs.keys(), not_none())
        assert_that(self.nginx_configs.keys(), has_length(0))

        config = self.nginx_configs[('/etc/nginx/nginx.conf', '/usr/share/nginx', '/usr/sbin/nginx')]

        assert_that(self.nginx_configs.keys(), has_length(1))
        assert_that(self.nginx_configs.keys(), equal_to([('/etc/nginx/nginx.conf', '/usr/share/nginx', '/usr/sbin/nginx')]))

    def test_get(self):
        assert_that(self.nginx_configs, has_length(0))

        config = self.nginx_configs[('/etc/nginx/nginx.conf', '/usr/share/nginx', '/usr/sbin/nginx')]
        assert_that(config, not_none())
        assert_that(config, instance_of(NginxConfig))

        assert_that(self.nginx_configs, has_length(1))

    def test_del(self):
        assert_that(self.nginx_configs, has_length(0))

        config = self.nginx_configs[('/etc/nginx/nginx.conf', '/usr/share/nginx', '/usr/sbin/nginx')]
        assert_that(config, not_none())
        assert_that(config, instance_of(NginxConfig))

        assert_that(self.nginx_configs, has_length(1))

        del self.nginx_configs[('/etc/nginx/nginx.conf', '/usr/share/nginx', '/usr/sbin/nginx')]

        assert_that(self.nginx_configs, has_length(0))


class NginxConfigTankCleanTestCase(RealNginxTestCase):
    def setup_method(self, method):
        super(NginxConfigTankCleanTestCase, self).setup_method(method)

        # rejuvanate context for this test in case it was polluted before
        context.nginx_configs = None
        context.nginx_configs = NginxConfigTank()

    def teardown_method(self, method):
        # rejuvanate context for future tests
        context.nginx_configs = None
        context.nginx_configs = NginxConfigTank()

        super(NginxConfigTankCleanTestCase, self).teardown_method(method)

    def test_discover(self):
        assert_that(context.nginx_configs, has_length(0))

        # init manager and make sure that object count is 0
        manager = NginxManager()
        assert_that(context.objects.find_all(types=manager.types), has_length(0))

        # discover objects and make sure that there is now 1 managed nginx object
        manager._discover_objects()
        assert_that(context.objects.find_all(types=manager.types), has_length(1))

        # check to see that there is now one nginx config
        assert_that(context.nginx_configs, has_length(1))

    def test_clean(self):
        manager = NginxManager()
        manager._discover_objects()

        # check to see that there is now one nginx config
        assert_that(context.nginx_configs, has_length(1))

        self.stop_first_nginx()

        manager._discover_objects()

        # check to see that nginx object removed
        assert_that(context.objects.find_all(types=manager.types), has_length(0))

        # check that the nginx config is also removed
        assert_that(context.nginx_configs, has_length(0))

        # restart nginx to avoid teardown error
        self.start_first_nginx()
