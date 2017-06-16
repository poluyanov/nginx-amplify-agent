# -*- coding: utf-8 -*-
import time
from hamcrest import (
    assert_that, calling, raises, not_
)

from test.base import BaseTestCase

from amplify.agent.common.util.timeout import timeout, TimeoutException


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov",
    "Andrew Alexeev", "Grant Hulegaard", "Arie van Luttikhuizen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class TimoutUtilTestCase(BaseTestCase):
    def test_basic_timeout(self):
        @timeout(1)
        def _endless_func():
            while True:
                continue

        assert_that(
            calling(_endless_func),
            raises(TimeoutException)
        )

    def test_basic_no_timeout(self):
        @timeout(3)
        def _two_second_func():
            for i in range(2):
                time.sleep(1)

        assert_that(
            calling(_two_second_func),
            not_(raises(TimeoutException))
        )
