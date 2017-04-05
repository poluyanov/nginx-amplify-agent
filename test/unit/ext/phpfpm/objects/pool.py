# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.ext.phpfpm.objects.pool import PHPFPMPoolObject


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMPoolObjectTestCase(BaseTestCase):
    """
    Test case for PHPFPMPoolObject.
    """

    def test_init(self):
        pool_data = {
            'status_path': '/status',
            'name': 'www',
            'file': '/etc/php5/fpm/pool.d/www.conf',
            'listen': '/run/php/php7.0-fpm.sock'
        }

        phpfpm_pool = PHPFPMPoolObject(
            local_id=124,
            parent_local_id=123,
            **pool_data
        )

        assert_that(phpfpm_pool, not_none())
        assert_that(phpfpm_pool.parent_local_id, equal_to(123))
        assert_that(phpfpm_pool.local_id_args, equal_to((123, 'www')))
        assert_that(phpfpm_pool.local_id, equal_to(124))
        assert_that(phpfpm_pool.definition, equal_to(
            {'local_id': 124, 'type': 'phpfpm_pool', 'root_uuid': None}
        ))
        assert_that(phpfpm_pool.definition_hash, equal_to(
            '8c84685602a25812172c511118d0f93d705f2cd67c41d278f4ae5b8b8967a8bd'
        ))
        assert_that(phpfpm_pool.collectors, has_length(2))
