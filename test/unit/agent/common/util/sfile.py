# -*- coding: utf-8 -*-
from hamcrest import *

from test.base import BaseTestCase

from amplify.agent.common.util.sfile import StringFile


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov",
    "Andrew Alexeev", "Grant Hulegaard", "Arie van Luttikhuizen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class StringFileTestCase(BaseTestCase):
    def test_simple(self):
        with StringFile() as f:
            f.write('line\n')
            f.write('line2')

            assert_that(str(f), equal_to('line\nline2'))
            assert_that(f, has_length(2))

            f.write('\nline3\n')

            assert_that(str(f), equal_to('line\nline2\nline3\n'))
            assert_that(f, has_length(4))

    def test_init(self):
        with StringFile('line\nline2') as f:
            assert_that(str(f), equal_to('line\nline2'))
            assert_that(f, has_length(2))

    def test_iter(self):
        with StringFile('line\nline2') as f:
            for line in f:
                assert_that(line.startswith('line'), equal_to(True))
                assert_that(line, is_in(('line', 'line2')))

    def test_slicing(self):
        with StringFile('1\n2\n3\n4\n') as f:
            sliced = f[2:]
            assert_that(sliced, has_length(3))
            assert_that(sliced, equal_to(['3', '4', '']))

    def test_readline(self):
        with StringFile('line\nline2') as f:
            line1 = f.readline()
            assert_that(line1, equal_to('line'))

            line2 = f.readline()
            assert_that(line2, equal_to('line2'))
