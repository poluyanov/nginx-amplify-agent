# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.util.cycle import cycle


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class CycleTestCase(BaseTestCase):
    def test_simple(self):
        cycler = cycle(3)
        assert_that(cycler.next(), equal_to(0))
        assert_that(cycler.next(), equal_to(1))
        assert_that(cycler.next(), equal_to(2))
        assert_that(cycler.next(), equal_to(3))
        assert_that(cycler.next(), equal_to(0))

        cycler = cycle(7, 10)
        assert_that(cycler.next(), equal_to(7))
        assert_that(cycler.next(), equal_to(8))
        assert_that(cycler.next(), equal_to(9))
        assert_that(cycler.next(), equal_to(10))
        assert_that(cycler.next(), equal_to(7))

        cycler = cycle(stop=10, step=2)
        assert_that(cycler.next(), equal_to(0))
        assert_that(cycler.next(), equal_to(2))
        assert_that(cycler.next(), equal_to(4))
        assert_that(cycler.next(), equal_to(6))
        assert_that(cycler.next(), equal_to(8))
        assert_that(cycler.next(), equal_to(10))
        assert_that(cycler.next(), equal_to(0))
