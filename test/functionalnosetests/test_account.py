#!/usr/bin/python

# Copyright (c) 2010-2012 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from nose import SkipTest

from swift.common.constraints import MAX_META_COUNT, MAX_META_NAME_LENGTH, \
    MAX_META_OVERALL_SIZE, MAX_META_VALUE_LENGTH

from swift_testing import check_response, retry, skip, web_front_end


class TestAccount(unittest.TestCase):

    def test_metadata(self):
        if skip:
            raise SkipTest

        def post(url, token, parsed, conn, value):
            conn.request('POST', parsed.path, '',
                         {'X-Auth-Token': token, 'X-Account-Meta-Test': value})
            return check_response(conn)

        def head(url, token, parsed, conn):
            conn.request('HEAD', parsed.path, '', {'X-Auth-Token': token})
            return check_response(conn)

        def get(url, token, parsed, conn):
            conn.request('GET', parsed.path, '', {'X-Auth-Token': token})
            return check_response(conn)

        resp = retry(post, '')
        resp.read()
        self.assertEquals(resp.status, 204)
        resp = retry(head)
        resp.read()
        self.assert_(resp.status in (200, 204), resp.status)
        self.assertEquals(resp.getheader('x-account-meta-test'), None)
        resp = retry(get)
        resp.read()
        self.assert_(resp.status in (200, 204), resp.status)
        self.assertEquals(resp.getheader('x-account-meta-test'), None)
        resp = retry(post, 'Value')
        resp.read()
        self.assertEquals(resp.status, 204)
        resp = retry(head)
        resp.read()
        self.assert_(resp.status in (200, 204), resp.status)
        self.assertEquals(resp.getheader('x-account-meta-test'), 'Value')
        resp = retry(get)
        resp.read()
        self.assert_(resp.status in (200, 204), resp.status)
        self.assertEquals(resp.getheader('x-account-meta-test'), 'Value')

    def test_unicode_metadata(self):
        if skip:
            raise SkipTest

        def post(url, token, parsed, conn, name, value):
            conn.request('POST', parsed.path, '',
                         {'X-Auth-Token': token, name: value})
            return check_response(conn)

        def head(url, token, parsed, conn):
            conn.request('HEAD', parsed.path, '', {'X-Auth-Token': token})
            return check_response(conn)
        uni_key = u'X-Account-Meta-uni\u0E12'
        uni_value = u'uni\u0E12'
        if (web_front_end == 'integral'):
            resp = retry(post, uni_key, '1')
            resp.read()
            self.assertTrue(resp.status in (201, 204))
            resp = retry(head)
            resp.read()
            self.assert_(resp.status in (200, 204), resp.status)
            self.assertEquals(resp.getheader(uni_key.encode('utf-8')), '1')
        resp = retry(post, 'X-Account-Meta-uni', uni_value)
        resp.read()
        self.assertEquals(resp.status, 204)
        resp = retry(head)
        resp.read()
        self.assert_(resp.status in (200, 204), resp.status)
        self.assertEquals(resp.getheader('X-Account-Meta-uni'),
                          uni_value.encode('utf-8'))
        if (web_front_end == 'integral'):
            resp = retry(post, uni_key, uni_value)
            resp.read()
            self.assertEquals(resp.status, 204)
            resp = retry(head)
            resp.read()
            self.assert_(resp.status in (200, 204), resp.status)
            self.assertEquals(resp.getheader(uni_key.encode('utf-8')),
                              uni_value.encode('utf-8'))

    def test_multi_metadata(self):
        if skip:
            raise SkipTest

        def post(url, token, parsed, conn, name, value):
            conn.request('POST', parsed.path, '',
                         {'X-Auth-Token': token, name: value})
            return check_response(conn)

        def head(url, token, parsed, conn):
            conn.request('HEAD', parsed.path, '', {'X-Auth-Token': token})
            return check_response(conn)

        resp = retry(post, 'X-Account-Meta-One', '1')
        resp.read()
        self.assertEquals(resp.status, 204)
        resp = retry(head)
        resp.read()
        self.assert_(resp.status in (200, 204), resp.status)
        self.assertEquals(resp.getheader('x-account-meta-one'), '1')
        resp = retry(post, 'X-Account-Meta-Two', '2')
        resp.read()
        self.assertEquals(resp.status, 204)
        resp = retry(head)
        resp.read()
        self.assert_(resp.status in (200, 204), resp.status)
        self.assertEquals(resp.getheader('x-account-meta-one'), '1')
        self.assertEquals(resp.getheader('x-account-meta-two'), '2')

    def test_bad_metadata(self):
        if skip:
            raise SkipTest

        def post(url, token, parsed, conn, extra_headers):
            headers = {'X-Auth-Token': token}
            headers.update(extra_headers)
            conn.request('POST', parsed.path, '', headers)
            return check_response(conn)

        resp = retry(post,
                     {'X-Account-Meta-' + ('k' * MAX_META_NAME_LENGTH): 'v'})
        resp.read()
        self.assertEquals(resp.status, 204)
        resp = retry(
            post,
            {'X-Account-Meta-' + ('k' * (MAX_META_NAME_LENGTH + 1)): 'v'})
        resp.read()
        self.assertEquals(resp.status, 400)

        resp = retry(post,
                     {'X-Account-Meta-Too-Long': 'k' * MAX_META_VALUE_LENGTH})
        resp.read()
        self.assertEquals(resp.status, 204)
        resp = retry(
            post,
            {'X-Account-Meta-Too-Long': 'k' * (MAX_META_VALUE_LENGTH + 1)})
        resp.read()
        self.assertEquals(resp.status, 400)

        headers = {}
        for x in xrange(MAX_META_COUNT):
            headers['X-Account-Meta-%d' % x] = 'v'
        resp = retry(post, headers)
        resp.read()
        self.assertEquals(resp.status, 204)
        headers = {}
        for x in xrange(MAX_META_COUNT + 1):
            headers['X-Account-Meta-%d' % x] = 'v'
        resp = retry(post, headers)
        resp.read()
        self.assertEquals(resp.status, 400)

        headers = {}
        header_value = 'k' * MAX_META_VALUE_LENGTH
        size = 0
        x = 0
        while size < MAX_META_OVERALL_SIZE - 4 - MAX_META_VALUE_LENGTH:
            size += 4 + MAX_META_VALUE_LENGTH
            headers['X-Account-Meta-%04d' % x] = header_value
            x += 1
        if MAX_META_OVERALL_SIZE - size > 1:
            headers['X-Account-Meta-k'] = \
                'v' * (MAX_META_OVERALL_SIZE - size - 1)
        resp = retry(post, headers)
        resp.read()
        self.assertEquals(resp.status, 204)
        headers['X-Account-Meta-k'] = \
            'v' * (MAX_META_OVERALL_SIZE - size)
        resp = retry(post, headers)
        resp.read()
        self.assertEquals(resp.status, 400)


if __name__ == '__main__':
    unittest.main()
