# -*- coding: utf-8 -*-
from hamcrest import (
    assert_that, not_none, equal_to, string_contains_in_order, calling, raises,
    has_length, not_
)
import os

from test.base import disabled_test
from test.unit.ext.phpfpm.base import PHPFPMTestCase

from amplify.agent.common.util.ps import subp
from amplify.agent.common.errors import AmplifySubprocessError

from amplify.ext.phpfpm.util.ps import (
    PS_CMD, PS_PARSER, MASTER_PARSER, LS_CMD, LS_PARSER
)
from amplify.ext.phpfpm.util.inet import INET_IPV4
from amplify.ext.phpfpm.util.fpmstatus import PHPFPMStatus
from amplify.ext.phpfpm.util.parser import PHPFPMConfig
from amplify.ext.phpfpm.util.version import VERSION_PARSER


__author__ = "Grant Hulegaard"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = [
    "Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev", "Grant Hulegaard",
    "Arie van Luttikhuizen", "Jason Thigpen"
]
__license__ = ""
__maintainer__ = "Grant Hulegaard"
__email__ = "grant.hulegaard@nginx.com"


class PHPFPMUtilsTestCase(PHPFPMTestCase):
    """
    Test case for basic utilities
    """

    def test_ps_cmd(self):
        ps, _ = subp.call(PS_CMD)

        assert_that(ps, not_none())
        assert_that(ps, has_length(4))  # TODO: Try to eliminate blank line capture from ps (at end)
        assert_that(ps[0], string_contains_in_order('php-fpm:', 'master', 'process', 'php-fpm.conf'))
        for child in ps[1:-1]:
            assert_that(child, string_contains_in_order('php-fpm:', 'pool', 'www'))
        assert_that(ps[-1], equal_to(''))  # Try to eliminate this in future.

    def test_ps_cmd_phpfpm_off(self):
        self.stop_fpm()

        assert_that(calling(subp.call).with_args(PS_CMD), raises(AmplifySubprocessError))

    def test_ps_parser(self):
        ps, _ = subp.call(PS_CMD)
        assert_that(ps, not_none())

        parsed_lines = [PS_PARSER(line) for line in ps]
        assert_that(parsed_lines, not_none())
        assert_that(parsed_lines, has_length(4))

        # just for ease of testing, let's trim the None at the end
        parsed_lines = filter(lambda item: item is not None, parsed_lines)
        assert_that(parsed_lines, has_length(3))

        master_pid, master_ppid, master_command = parsed_lines[0]
        assert_that(master_pid, not_none())
        assert_that(master_ppid, equal_to(1))
        assert_that(master_command, string_contains_in_order('php-fpm:', 'master', 'process', 'php-fpm.conf'))

        for child_id, child_ppid, child_command in parsed_lines[1:]:
            assert_that(child_id, not_none())
            assert_that(child_ppid, equal_to(master_pid))
            assert_that(child_command, string_contains_in_order('php-fpm:', 'pool', 'www'))

    def test_ps_master_parser(self):
        ps, _ = subp.call(PS_CMD)
        assert_that(ps, not_none())

        parsed_lines = [PS_PARSER(line) for line in ps]
        assert_that(parsed_lines, not_none())
        assert_that(parsed_lines, has_length(4))

        master_pid, master_ppid, master_command = parsed_lines[0]

        parsed_master = MASTER_PARSER(master_command)
        assert_that(parsed_master, not_none())
        assert_that(parsed_master, equal_to('/etc/php5/fpm/php-fpm.conf'))

    def test_inet_ipv4(self):
        test_address = INET_IPV4(host='localhost', port=80)
        assert_that(test_address, not_none())
        assert_that(test_address.host, equal_to('localhost'))
        assert_that(test_address.port, equal_to(80))

        test_address_2 = INET_IPV4(host='localhost', port=81)
        assert_that(test_address_2, not_none())
        assert_that(test_address_2.host, equal_to('localhost'))
        assert_that(test_address_2.port, equal_to(81))
        assert_that(test_address_2, not_(equal_to(test_address)))

        test_address_3 = INET_IPV4(host='localhost1', port=80)
        assert_that(test_address_3, not_none())
        assert_that(test_address_3.host, equal_to('localhost1'))
        assert_that(test_address_3.port, equal_to(80))
        assert_that(test_address_3, not_(equal_to(test_address)))

        test_address_4 = INET_IPV4(host='localhost', port=80)
        assert_that(test_address_4, not_none())
        assert_that(test_address_4.host, equal_to('localhost'))
        assert_that(test_address_4.port, equal_to(80))
        assert_that(test_address_4, equal_to(test_address))

    def test_ls_cmd(self):
        ps, _ = subp.call(PS_CMD)
        parsed_lines = [PS_PARSER(line) for line in ps]
        master_pid, master_ppid, master_command = parsed_lines[0]

        ls, _ = subp.call(LS_CMD % master_pid)
        assert_that(ls, not_none())

    def test_ls_parser(self):
        ps, _ = subp.call(PS_CMD)
        parsed_lines = [PS_PARSER(line) for line in ps]
        master_pid, master_ppid, master_command = parsed_lines[0]

        ls, _ = subp.call(LS_CMD % master_pid)
        assert_that(ls, not_none())

        parsed = LS_PARSER(ls[0])
        assert_that(parsed, not_none())
        assert_that(parsed, equal_to('/usr/sbin/php5-fpm'))

    def test_version_parser(self):
        # get master_pid
        ps, _ = subp.call(PS_CMD)
        ps_parsed_lines = [PS_PARSER(line) for line in ps]
        master_pid, master_ppid, master_command = ps_parsed_lines[0]

        # get bin_path
        ls, _ = subp.call(LS_CMD % master_pid)
        bin_path = LS_PARSER(ls[0])

        version, raw_line = VERSION_PARSER(bin_path)
        assert_that(version, not_none())
        assert_that(raw_input, not_none)

        # these checks may be too specific...will definitely break on alternate
        # systems/versions
        assert_that(version, equal_to('5.5.9-1'))
        assert_that(raw_line, equal_to(
            'PHP 5.5.9-1ubuntu4.21 (fpm-fcgi) (built: Feb  9 2017 21:00:52)'
        ))


class PHPFPMStatusTestCase(PHPFPMTestCase):
    """
    Test case for status page query.  This implicitly tests FCGIApp as well.
    """

    def test_basic_unix(self):
        pool_status = PHPFPMStatus(path='/run/php/php7.0-fpm.sock', url='/status')
        page = pool_status.get_status()

        """
        pool:                 www
        process manager:      dynamic
        start time:           07/Dec/2016:00:13:21 +0000
        start since:          0
        accepted conn:        1
        listen queue:         0
        max listen queue:     0
        listen queue len:     0
        idle processes:       0
        active processes:     1
        total processes:      1
        max active processes: 1
        max children reached: 0
        slow requests:        0
        """

        assert_that(page, not_none())
        assert_that(page.count('\n'), equal_to(14))

    # this is disabled because our default php-fpm config only has a unix socket.
    @disabled_test
    def test_basic_ipv4(self):
        pool_status = PHPFPMStatus(host='127.0.0.1', port=51, url='/status')
        page = pool_status.get_status()

        """
        pool:                 www
        process manager:      dynamic
        start time:           07/Dec/2016:00:13:21 +0000
        start since:          0
        accepted conn:        1
        listen queue:         0
        max listen queue:     0
        listen queue len:     0
        idle processes:       0
        active processes:     1
        total processes:      1
        max active processes: 1
        max children reached: 0
        slow requests:        0
        """

        assert_that(page, not_none())
        assert_that(page.count('\n'), equal_to(14))


class PHPFPMConfigTestCase(PHPFPMTestCase):
    def test_old_working_file(self):
        config = PHPFPMConfig(path='/etc/php5/fpm/php-fpm.conf')
        assert_that(config, not_none())
        assert_that(config.parsed, equal_to(
            {
                'pools': [
                    {
                        'status_path': '/status',
                        'name': 'www',
                        'file': '/etc/php5/fpm/pool.d/www.conf',
                        'listen': '/run/php/php7.0-fpm.sock'
                    }
                ],
                'include': ['/etc/php5/fpm/pool.d/*.conf'],
                'file': '/etc/php5/fpm/php-fpm.conf'
            }
        ))

    def test_new_format(self):
        conf = os.getcwd() + '/test/fixtures/phpfpm/new_format/php-fpm.conf'

        config = PHPFPMConfig(path=conf)
        assert_that(config, not_none())
        assert_that(config.parsed, equal_to(
            {
                'pools': [
                    {
                        'status_path': '/status',
                        'name': 'www',
                        'file': '/amplify/test/fixtures/phpfpm/new_format/'
                                'php-fpm-7.0.d/www.conf',
                        'listen': '127.0.0.1:9000'
                    }
                ],
                'include': ['php-fpm-7.0.d/*.conf'],
                'file': '/amplify/test/fixtures/phpfpm/new_format/php-fpm.conf'
            }
        ))

    def test_new_format_multi_pool(self):
        conf = os.getcwd() + '/test/fixtures/phpfpm/new_format_multi_pool/' \
                             'php-fpm.conf'

        config = PHPFPMConfig(path=conf)
        assert_that(config, not_none())
        assert_that(config.parsed, equal_to(
            {
                'pools': [
                    {
                        'status_path': '/php_status',
                        'name': 'www',
                        'file': '/amplify/test/fixtures/phpfpm/new_format_'
                                'multi_pool/php-fpm.d/www.conf',
                        'listen': '9000'
                    },
                    {
                        'status_path': '/php_status',
                        'name': 'www-socket',
                        'file': '/amplify/test/fixtures/phpfpm/new_format_'
                                'multi_pool/php-fpm.d/www-socket.conf',
                        'listen': '/var/run/php5-fpm.sock'
                    }
                ],
                'include': ['php-fpm.d/*.conf'],
                'file': '/amplify/test/fixtures/phpfpm/new_format_multi_pool'
                        '/php-fpm.conf'
            }
        ))

    def test_new_format_no_include(self):
        conf = os.getcwd() + '/test/fixtures/phpfpm/new_format_no_include/' \
                             'php-fpm.conf'

        config = PHPFPMConfig(path=conf)
        assert_that(config, not_none())
        assert_that(config.parsed, equal_to(
            {
                'pools': [],
                'include': [],
                'file': '/amplify/test/fixtures/phpfpm/new_format_no_include'
                        '/php-fpm.conf'
            }
        ))

    def test_new_format_no_values(self):
        conf = os.getcwd() + '/test/fixtures/phpfpm/new_format_no_values' \
                             '/php-fpm.conf'

        config = PHPFPMConfig(path=conf)
        assert_that(config, not_none())
        assert_that(config.parsed, equal_to(
            {
                'pools': [
                    {
                        'status_path': None,
                        'name': 'www',
                        'file': '/amplify/test/fixtures/phpfpm/new_format_'
                                'no_values/php-fpm.d/www.conf',
                        'listen': '9000'
                    },
                    {
                        'status_path': '/php_status',
                        'name': 'www-socket',
                        'file': '/amplify/test/fixtures/phpfpm/new_format_'
                                'no_values/php-fpm.d/www-socket.conf',
                        'listen': None
                    }
                ],
                'include': ['php-fpm.d/*.conf'],
                'file': '/amplify/test/fixtures/phpfpm/new_format_no_values'
                        '/php-fpm.conf'
            }
        ))
