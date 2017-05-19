# -*- coding: utf-8 -*-
from hamcrest import *

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

    def test_old_working_file_as_buffer(self):
        sbuff = """
[global]
; Pid file
; Note: the default prefix is /var
; Default Value: none
pid = /var/run/php5-fpm.pid

; Error log file
; If it's set to "syslog", log is sent to syslogd instead of being written
; in a local file.
; Note: the default prefix is /var
; Default Value: log/php-fpm.log
error_log = /var/log/php5-fpm.log

; syslog_facility is used to specify what type of program is logging the
; message. This lets syslogd specify that messages from different facilities
; will be handled differently.
; See syslog(3) for possible values (ex daemon equiv LOG_DAEMON)
; Default Value: daemon
;syslog.facility = daemon

; syslog_ident is prepended to every message. If you have multiple FPM
; instances running on the same server, you can change the default value
; which must suit common needs.
; Default Value: php-fpm
;syslog.ident = php-fpm

; Log level
; Possible Values: alert, error, warning, notice, debug
; Default Value: notice
;log_level = notice

; If this number of child processes exit with SIGSEGV or SIGBUS within the time
; interval set by emergency_restart_interval then FPM will restart. A value
; of '0' means 'Off'.
; Default Value: 0
;emergency_restart_threshold = 0

; Interval of time used by emergency_restart_interval to determine when
; a graceful restart will be initiated.  This can be useful to work around
; accidental corruptions in an accelerator's shared memory.
; Available Units: s(econds), m(inutes), h(ours), or d(ays)
; Default Unit: seconds
; Default Value: 0
;emergency_restart_interval = 0

; Time limit for child processes to wait for a reaction on signals from master.
; Available units: s(econds), m(inutes), h(ours), or d(ays)
; Default Unit: seconds
; Default Value: 0
;process_control_timeout = 0

; The maximum number of processes FPM will fork. This has been design to control
; the global number of processes when using dynamic PM within a lot of pools.
; Use it with caution.
; Note: A value of 0 indicates no limit
; Default Value: 0
; process.max = 128

; Specify the nice(2) priority to apply to the master process (only if set)
; The value can vary from -19 (highest priority) to 20 (lower priority)
; Note: - It will only work if the FPM master process is launched as root
;       - The pool process will inherit the master process priority
;         unless it specified otherwise
; Default Value: no set
; process.priority = -19

; Send FPM to background. Set to 'no' to keep FPM in foreground for debugging.
; Default Value: yes
;daemonize = yes

; Set open file descriptor rlimit for the master process.
; Default Value: system defined value
;rlimit_files = 1024

; Set max core size rlimit for the master process.
; Possible Values: 'unlimited' or an integer greater or equal to 0
; Default Value: system defined value
;rlimit_core = 0

; Specify the event mechanism FPM will use. The following is available:
; - select     (any POSIX os)
; - poll       (any POSIX os)
; - epoll      (linux >= 2.5.44)
; - kqueue     (FreeBSD >= 4.1, OpenBSD >= 2.9, NetBSD >= 2.0)
; - /dev/poll  (Solaris >= 7)
; - port       (Solaris >= 10)
; Default Value: not set (auto detection)
;events.mechanism = epoll

; When FPM is build with systemd integration, specify the interval,
; in second, between health report notification to systemd.
; Set to 0 to disable.
; Available Units: s(econds), m(inutes), h(ours)
; Default Unit: seconds
; Default value: 10
;systemd_interval = 10

;;;;;;;;;;;;;;;;;;;;
; Pool Definitions ;
;;;;;;;;;;;;;;;;;;;;

; Multiple pools of child processes may be started with different listening
; ports and different management options.  The name of the pool will be
; used in logs and stats. There is no limitation on the number of pools which
; FPM can handle. Your system will tell you anyway :)

; To configure the pools it is recommended to have one .conf file per
; pool in the following directory:
include=/etc/php5/fpm/pool.d/*.conf

        """

        config = PHPFPMConfig()
        assert_that(config, not_none())

        config.readb(sbuff)
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
                'file': None
            }
        ))

    def test_new_broken_file(self):
        sbuff = """
; To configure the pools it is recommended to have one .conf file per
; pool in the following directory:
include=/etc/php5/fpm/pool.d/*.conf

[global]
; Pid file
; Note: the default prefix is /var
; Default Value: none
pid = /var/run/php5-fpm.pid

; Error log file
; If it's set to "syslog", log is sent to syslogd instead of being written
; in a local file.
; Note: the default prefix is /var
; Default Value: log/php-fpm.log
error_log = /var/log/php5-fpm.log

; syslog_facility is used to specify what type of program is logging the
; message. This lets syslogd specify that messages from different facilities
; will be handled differently.
; See syslog(3) for possible values (ex daemon equiv LOG_DAEMON)
; Default Value: daemon
;syslog.facility = daemon

; syslog_ident is prepended to every message. If you have multiple FPM
; instances running on the same server, you can change the default value
; which must suit common needs.
; Default Value: php-fpm
;syslog.ident = php-fpm

; Log level
; Possible Values: alert, error, warning, notice, debug
; Default Value: notice
;log_level = notice

; If this number of child processes exit with SIGSEGV or SIGBUS within the time
; interval set by emergency_restart_interval then FPM will restart. A value
; of '0' means 'Off'.
; Default Value: 0
;emergency_restart_threshold = 0

; Interval of time used by emergency_restart_interval to determine when
; a graceful restart will be initiated.  This can be useful to work around
; accidental corruptions in an accelerator's shared memory.
; Available Units: s(econds), m(inutes), h(ours), or d(ays)
; Default Unit: seconds
; Default Value: 0
;emergency_restart_interval = 0

; Time limit for child processes to wait for a reaction on signals from master.
; Available units: s(econds), m(inutes), h(ours), or d(ays)
; Default Unit: seconds
; Default Value: 0
;process_control_timeout = 0

; The maximum number of processes FPM will fork. This has been design to control
; the global number of processes when using dynamic PM within a lot of pools.
; Use it with caution.
; Note: A value of 0 indicates no limit
; Default Value: 0
; process.max = 128

; Specify the nice(2) priority to apply to the master process (only if set)
; The value can vary from -19 (highest priority) to 20 (lower priority)
; Note: - It will only work if the FPM master process is launched as root
;       - The pool process will inherit the master process priority
;         unless it specified otherwise
; Default Value: no set
; process.priority = -19

; Send FPM to background. Set to 'no' to keep FPM in foreground for debugging.
; Default Value: yes
;daemonize = yes

; Set open file descriptor rlimit for the master process.
; Default Value: system defined value
;rlimit_files = 1024

; Set max core size rlimit for the master process.
; Possible Values: 'unlimited' or an integer greater or equal to 0
; Default Value: system defined value
;rlimit_core = 0

; Specify the event mechanism FPM will use. The following is available:
; - select     (any POSIX os)
; - poll       (any POSIX os)
; - epoll      (linux >= 2.5.44)
; - kqueue     (FreeBSD >= 4.1, OpenBSD >= 2.9, NetBSD >= 2.0)
; - /dev/poll  (Solaris >= 7)
; - port       (Solaris >= 10)
; Default Value: not set (auto detection)
;events.mechanism = epoll

; When FPM is build with systemd integration, specify the interval,
; in second, between health report notification to systemd.
; Set to 0 to disable.
; Available Units: s(econds), m(inutes), h(ours)
; Default Unit: seconds
; Default value: 10
;systemd_interval = 10

;;;;;;;;;;;;;;;;;;;;
; Pool Definitions ;
;;;;;;;;;;;;;;;;;;;;

; Multiple pools of child processes may be started with different listening
; ports and different management options.  The name of the pool will be
; used in logs and stats. There is no limitation on the number of pools which
; FPM can handle. Your system will tell you anyway :)

        """

        config = PHPFPMConfig()
        assert_that(config, not_none())

        config.readb(sbuff)
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
                'file': None
            }
        ))
