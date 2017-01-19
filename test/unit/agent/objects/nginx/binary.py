# -*- coding: utf-8 -*-
from hamcrest import *

from amplify.agent.objects.nginx.binary import get_prefix_and_conf_path, nginx_v
from test.base import BaseTestCase, TestWithFakeSubpCall

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__credits__ = ["Mike Belov", "Andrei Belov", "Ivan Poluyanov", "Oleg Mamontov", "Andrew Alexeev"]
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


class NginxVersionInfoTestCase(TestWithFakeSubpCall):

    def test_1_10_1_openssl_oss(self):
        self.push_subp_result(
            stdout_lines=[],
            stderr_lines=[
                'nginx version: nginx/1.10.1',
                'built by clang 7.0.2 (clang-700.1.81)',
                'built with OpenSSL 1.0.2h  3 May 2016',
                'TLS SNI support enabled'
            ]
        )
        assert_that(nginx_v('xyz'), has_entries(
            version='1.10.1',
            ssl=has_entries(
                built=contains('OpenSSL', '1.0.2h', '3 May 2016'),
                run=contains('OpenSSL', '1.0.2h', '3 May 2016')
            ),
            plus=has_entries(enabled=False, release=None),
            configure=empty()
        ))

    def test_1_11_3_openssl_plus(self):
        self.push_subp_result(
            stdout_lines=[],
            stderr_lines=[
                'nginx version: nginx/1.11.3 (nginx-plus-r10)',
                'built by gcc 5.4.0 20160609 (Ubuntu 5.4.0-6ubuntu1~16.04.2)',
                'built with OpenSSL 1.0.2g-fips 1 Mar 2016 (running with OpenSSL 1.0.2g 1 Mar 2016)',
                'TLS SNI support enabled'
            ]
        )
        assert_that(nginx_v('xyz'), has_entries(
            version='1.11.3',
            ssl=has_entries(
                built=contains('OpenSSL', '1.0.2g-fips', '1 Mar 2016'),
                run=contains('OpenSSL', '1.0.2g', '1 Mar 2016')
            ),
            plus=has_entries(enabled=True, release='nginx-plus-r10'),
            configure=empty()
        ))

    def test_1_11_8_libressl(self):
        self.push_subp_result(
            stdout_lines=[],
            stderr_lines=[
                'nginx version: nginx/1.11.8',
                'built by gcc 6.3.0 20161229 (Debian 6.3.0-2)',
                'built with LibreSSL 2.5.0',
                'TLS SNI support enabled'
            ]
        )
        assert_that(nginx_v('foo'), has_entries(
            version='1.11.8',
            ssl=has_entries(
                built=contains('LibreSSL', '2.5.0', None),
                run=contains('LibreSSL', '2.5.0', None)
            ),
            plus=has_entries(enabled=False, release=None),
            configure=empty()
        ))

    def test_1_11_2_open_resty(self):
        self.push_subp_result(
            stdout_lines=[],
            stderr_lines=[
                'nginx version: openresty/1.11.2.2',
                'built by gcc 4.4.7 20120313 (Red Hat 4.4.7-17) (GCC)',
                'built with OpenSSL 1.0.2j  26 Sep 2016',
                'TLS SNI support enabled',
                "configure arguments: " + (
                    "--prefix=/usr/local/openresty/nginx --with-cc-opt='-O2 -I/usr/local/openresty/zlib/include "
                    "-I/usr/local/openresty/pcre/include -I/usr/local/openresty/openssl/include' "
                    "--add-module=../ngx_devel_kit-0.3.0 --add-module=../echo-nginx-module-0.60 "
                    "--add-module=../xss-nginx-module-0.05 --add-module=../ngx_coolkit-0.2rc3 "
                    "--add-module=../set-misc-nginx-module-0.31 --add-module=../form-input-nginx-module-0.12 "
                    "--add-module=../encrypted-session-nginx-module-0.06 --add-module=../srcache-nginx-module-0.31 "
                    "--add-module=../ngx_lua-0.10.7 --add-module=../ngx_lua_upstream-0.06 "
                    "--add-module=../headers-more-nginx-module-0.32 --add-module=../array-var-nginx-module-0.05 "
                    "--add-module=../memc-nginx-module-0.17 --add-module=../redis2-nginx-module-0.13 "
                    "--add-module=../redis-nginx-module-0.3.7 --with-ld-opt='-Wl,-rpath,"
                    "/usr/local/openresty/luajit/lib -L/usr/local/openresty/zlib/lib -L/usr/local/openresty/pcre/lib "
                    "-L/usr/local/openresty/openssl/lib -Wl,-rpath,"
                    "/usr/local/openresty/zlib/lib:/usr/local/openresty/pcre/lib:/usr/local/openresty/openssl/lib' "
                    "--with-pcre-jit --with-ipv6 --with-stream --with-stream_ssl_module --with-http_v2_module "
                    "--without-mail_pop3_module --without-mail_imap_module --without-mail_smtp_module "
                    "--with-http_stub_status_module --with-http_realip_module --with-http_addition_module "
                    "--with-http_auth_request_module --with-http_secure_link_module --with-http_random_index_module "
                    "--with-http_gzip_static_module --with-http_sub_module --with-http_dav_module "
                    "--with-http_flv_module --with-http_mp4_module --with-http_gunzip_module --with-threads "
                    "--with-file-aio --with-dtrace-probes --with-http_ssl_module"
                )
            ]
        )
        assert_that(nginx_v('foo'), has_entries({
            'version': '1.11.2.2',
            'ssl': has_entries({
                'built': contains('OpenSSL', '1.0.2j', '26 Sep 2016'),
                'run': contains('OpenSSL', '1.0.2j', '26 Sep 2016')
            }),
            'plus': has_entries({'enabled': False, 'release': none()}),
            'configure': has_entries({
                'prefix': '/usr/local/openresty/nginx',
                'with-cc-opt': (
                    "'-O2 -I/usr/local/openresty/zlib/include -I/usr/local/openresty/pcre/include "
                    "-I/usr/local/openresty/openssl/include'"
                ),
                'with-ld-opt': (
                    "'-Wl,-rpath,/usr/local/openresty/luajit/lib -L/usr/local/openresty/zlib/lib "
                    "-L/usr/local/openresty/pcre/lib -L/usr/local/openresty/openssl/lib "
                    "-Wl,-rpath,/usr/local/openresty/zlib/lib:/usr/local/openresty/pcre/lib:/usr/local/openresty/openssl/lib'"
                ),
                'add-module': contains(
                    '../ngx_devel_kit-0.3.0', '../echo-nginx-module-0.60', '../xss-nginx-module-0.05',
                    '../ngx_coolkit-0.2rc3', '../set-misc-nginx-module-0.31', '../form-input-nginx-module-0.12',
                    '../encrypted-session-nginx-module-0.06', '../srcache-nginx-module-0.31', '../ngx_lua-0.10.7',
                    '../ngx_lua_upstream-0.06', '../headers-more-nginx-module-0.32', '../array-var-nginx-module-0.05',
                    '../memc-nginx-module-0.17', '../redis2-nginx-module-0.13', '../redis-nginx-module-0.3.7'
                )
            })
        }))


class PrefixConfigPathTestCase(BaseTestCase):
    """
    Cases are named with binary code

    Coding scheme:
    -c  -p  --prefix --conf-path
    0    0         0           1

    """

    def test_0000(self):
        # none specified
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx', {}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/usr/local/nginx'))
        assert_that(conf_path, equal_to('/usr/local/nginx/conf/nginx.conf'))

    def test_0001_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx', {'conf-path': '/etc/nginx/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/usr/local/nginx'))
        assert_that(conf_path, equal_to('/etc/nginx/nginx.conf'))

    def test_0001_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx', {'conf-path': 'dir/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/usr/local/nginx'))
        assert_that(conf_path, equal_to('/usr/local/nginx/dir/nginx.conf'))

    def test_0010(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx', {'prefix': '/var'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/conf/nginx.conf'))

    def test_0011_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx', {'prefix': '/var', 'conf-path': '/etc/nginx/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx/nginx.conf'))

    def test_0011_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx', {'prefix': '/var', 'conf-path': 'dir/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

    def test_0100(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var', {}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/conf/nginx.conf'))

    def test_0101_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var', {'conf-path': '/etc/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_0101_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var', {'conf-path': 'dir/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

    def test_0110(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var', {'prefix': '/foo'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/conf/nginx.conf'))

    def test_0111_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var', {'prefix': '/foo', 'conf-path': '/etc/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_0111_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var', {'prefix': '/foo', 'conf-path': 'dir/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

    def test_1000_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c /etc/nginx.conf', {}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/usr/local/nginx'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_1000_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c dir/nginx.conf', {}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/usr/local/nginx'))
        assert_that(conf_path, equal_to('/usr/local/nginx/dir/nginx.conf'))

    def test_1001_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c /etc/nginx.conf', {'conf-path': '/foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/usr/local/nginx'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_1001_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c dir/nginx.conf', {'conf-path': 'foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/usr/local/nginx'))
        assert_that(conf_path, equal_to('/usr/local/nginx/dir/nginx.conf'))

    def test_1010_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c /etc/nginx.conf', {'prefix': '/var'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_1010_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c dir/nginx.conf', {'prefix': '/var'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

    def test_1011_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c /etc/nginx.conf', {'prefix': '/var', 'conf-path': '/foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_1011_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -c dir/nginx.conf', {'prefix': '/var', 'conf-path': '/foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

    def test_1100_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var -c /etc/nginx.conf', {}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_1100_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var -c dir/nginx.conf', {}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

    def test_1101_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var -c /etc/nginx.conf', {'conf-path': '/foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_1101_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var -c dir/nginx.conf', {'conf-path': '/foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

    def test_1111_absolute(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var -c /etc/nginx.conf', {'prefix': '/var', 'conf-path': '/foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/etc/nginx.conf'))

    def test_1111_relative(self):
        bin_path, prefix, conf_path, version = get_prefix_and_conf_path(
            'nginx: master process nginx -p /var -c dir/nginx.conf', {'prefix': '/var', 'conf-path': '/foo/nginx.conf'}
        )
        assert_that(bin_path, equal_to('nginx'))
        assert_that(prefix, equal_to('/var'))
        assert_that(conf_path, equal_to('/var/dir/nginx.conf'))

