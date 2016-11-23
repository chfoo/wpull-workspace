import unittest

from wbull.format.url.parse import schemes_similar, split_query, parse_ipv4_int, \
    parse_ipv4_address, URLInfo, join_query


class URLTestCase(unittest.TestCase):
    def test_schemes_similar(self):
        self.assertTrue(schemes_similar('http', 'http'))
        self.assertTrue(schemes_similar('https', 'http'))
        self.assertTrue(schemes_similar('http', 'https'))
        self.assertTrue(schemes_similar('https', 'https'))
        self.assertTrue(schemes_similar('Https', 'https'))
        self.assertTrue(schemes_similar('http', 'Http'))

        self.assertFalse(schemes_similar('ftp', 'http'))
        self.assertTrue(schemes_similar('email', 'email'))

    def test_split_query(self):
        self.assertEqual([],
                         split_query('&'))
        self.assertEqual([('a', 'ð')],
                         split_query('a=ð'))
        self.assertEqual([('a', 'ð')],
                         split_query('a=ð&b'))
        self.assertEqual([('a', 'ð')],
                         split_query('a=ð&b='))
        self.assertEqual([('a', 'ð'), ('b', None), ('c', '')],
                         split_query('a=ð&b&c=', keep_blank_values=True))
        self.assertEqual([('a', 'ð'), ('b', '%2F')],
                         split_query('a=ð&b=%2F', decode_escape=False))
        self.assertEqual([('a', 'ð'), ('b', '/')],
                         split_query('a=ð&b=%2F'))

    def test_join_query(self):
        self.assertEqual('', join_query([]))
        self.assertEqual('a=1', join_query([('a', '1')]))
        self.assertEqual('a=1&b=&c', join_query([('a', '1'), ('b', ''), ('c', None)]))
        self.assertEqual('a%3D%26%2B=1=%26%2B', join_query([('a=&+', '1=&+')]))

    def test_parse_ipv4_int(self):
        self.assertEqual(15, parse_ipv4_int('0xf'))
        self.assertEqual(9, parse_ipv4_int('011'))
        self.assertEqual(91, parse_ipv4_int('91'))

    def test_parse_ipv4_addrses(self):
        self.assertEqual(
            '192.0.2.235', parse_ipv4_address('0xC0.0x00.0x02.0xEB').compressed
        )
        self.assertEqual(
            '192.0.2.235', parse_ipv4_address('0300.0000.0002.0353').compressed
        )
        self.assertEqual(
            '192.0.2.235', parse_ipv4_address('0xC00002EB').compressed
        )
        self.assertEqual(
            '192.0.2.235', parse_ipv4_address('3221226219').compressed
        )
        self.assertEqual(
            '192.0.2.235', parse_ipv4_address('030000001353').compressed
        )

        with self.assertRaises(ValueError):
            parse_ipv4_address('123.123')

        with self.assertRaises(ValueError):
            parse_ipv4_address('123.a.123.1')

        with self.assertRaises(ValueError):
            parse_ipv4_address('123.123.123.999')

        with self.assertRaises(ValueError):
            parse_ipv4_address('0x12.123.123.999')


class URLObjectTest(unittest.TestCase):
    def parse_equal(self, input_url: str, output_url: str):
        self.assertEqual(output_url, URLInfo.parse(input_url).url)

    def test_all_parts_http(self):
        url_info = URLInfo.parse(
            'HTTP://userName:p%40ss%3Aword@[Ab::1]:81'
            '/ásdF\u200C/ghjK?a=b=c&D#/?%41🐾'
        )
        self.assertEqual(
            'http://userName:p%40ss:word@[ab::1]:81'
            '/%C3%A1sdF%E2%80%8C/ghjK?a=b=c&D#/?%41🐾',
            url_info.url
        )
        self.assertEqual('http://userName:p%40ss:word@[ab::1]:81',
                         url_info.origin)
        self.assertEqual('http', url_info.scheme)
        self.assertEqual('userName:p%40ss:word@[ab::1]:81',
                         url_info.authority)
        self.assertEqual('userName:p%40ss:word', url_info.userinfo)
        self.assertEqual('userName', url_info.username)
        self.assertEqual('p@ss:word', url_info.password)
        self.assertEqual('[ab::1]:81', url_info.host)
        self.assertEqual('ab::1', url_info.hostname)
        self.assertEqual(81, url_info.port)
        self.assertEqual('/%C3%A1sdF%E2%80%8C/ghjK?a=b=c&D#/?%41🐾', url_info.resource)
        self.assertEqual('/%C3%A1sdF%E2%80%8C/ghjK', url_info.path)
        self.assertEqual('a=b=c&D', url_info.query)
        self.assertEqual('/?%41🐾', url_info.fragment)

    def test_parts_ftp(self):
        url_info = URLInfo.parse(
            'Ftp://N00B:hunter2@LocalHost.Example/mydocs/'
        )
        self.assertEqual(
            'ftp://N00B:hunter2@localhost.example/mydocs/', url_info.url
        )

        self.assertEqual('ftp', url_info.scheme)
        self.assertEqual('N00B:hunter2@localhost.example',
                         url_info.authority)
        self.assertEqual('/mydocs/', url_info.resource)
        self.assertEqual('N00B', url_info.username)
        self.assertEqual('hunter2', url_info.password)
        self.assertEqual('localhost.example', url_info.host)
        self.assertEqual('localhost.example', url_info.hostname)
        self.assertEqual(21, url_info.port)
        self.assertEqual('/mydocs/', url_info.path)
        self.assertFalse(url_info.query)
        self.assertFalse(url_info.fragment)

    def test_url_info_naked_scheme(self):
        self.parse_equal('Example.Com', 'http://example.com/')
        self.parse_equal('example.com/', 'http://example.com/')

        # With port
        self.parse_equal('example.com:8080', 'http://example.com:8080/')
        self.parse_equal(
            'example.com:8080/A:B', 'http://example.com:8080/A:B'
        )

        # With only leading slash
        self.parse_equal('//example.com', 'http://example.com/')
        self.parse_equal('//example.com/Blah', 'http://example.com/Blah')

        # Localhost
        self.parse_equal('localhost', 'http://localhost/')
        self.parse_equal('localhost:8080', 'http://localhost:8080/')
        self.parse_equal('localhost:8080/A:B', 'http://localhost:8080/A:B')

    def test_default_port(self):
        url_info = URLInfo.parse('https://example.com:443')
        self.assertEqual(443, url_info.port)
        self.assertEqual('example.com', url_info.host)

        url_info = URLInfo.parse('https://example.com:8080')
        self.assertEqual(8080, url_info.port)
        self.assertEqual('example.com:8080', url_info.host)

    def test_parse_unicode_in_parts(self):
        url_info = URLInfo.parse('http://¹:²@³🐾.test/¤?€#🐾')

        self.assertEqual('¹', url_info.username)
        self.assertEqual('²', url_info.password)
        self.assertEqual('xn--3-t42s.test', url_info.hostname)
        self.assertEqual('/%C2%A4', url_info.path)
        self.assertEqual('%E2%82%AC', url_info.query)
        self.assertEqual('🐾', url_info.fragment)

        self.assertEqual(
            'http://%C2%B9:%C2%B2@xn--3-t42s.test/%C2%A4?%E2%82%AC#🐾',
            url_info.url
        )

    def test_percent_encoding_normalization(self):
        self.parse_equal(
            'http://%c2%B9:%c2%a0@example.test/%C2%a4?%e2%82%aC%F0%9f%90%Be',
            'http://%C2%B9:%C2%A0@example.test/%C2%A4?%E2%82%AC%F0%9F%90%BE'
        )

    def test_encoding(self):
        url_info = URLInfo.parse('example.com/文字化け/?blah=文字化け',
                                 encoding='shift_jis')
        self.assertEqual(
            'http://example.com/%95%B6%8E%9A%89%BB%82%AF/'
            '?blah=%E6%96%87%E5%AD%97%E5%8C%96%E3%81%91',
            url_info.url
        )
        self.assertEqual(
            '/%95%B6%8E%9A%89%BB%82%AF/',
            url_info.path
        )
        self.assertEqual(
            'blah=%E6%96%87%E5%AD%97%E5%8C%96%E3%81%91',
            url_info.query
        )
        self.assertEqual('shift_jis', url_info.encoding)
        self.assertEqual('utf-8', url_info.query_encoding)

    def test_query_encoding(self):
        url_info = URLInfo.parse('example.com/文字化け/?blah=文字化け',
                                 query_encoding='shift_jis')
        self.assertEqual(
            'http://example.com/%E6%96%87%E5%AD%97%E5%8C%96%E3%81%91/'
            '?blah=%95%B6%8E%9A%89%BB%82%AF',
            url_info.url
        )
        self.assertEqual(
            '/%E6%96%87%E5%AD%97%E5%8C%96%E3%81%91/',
            url_info.path
        )
        self.assertEqual(
            'blah=%95%B6%8E%9A%89%BB%82%AF',
            url_info.query
        )
        self.assertEqual('utf-8', url_info.encoding)
        self.assertEqual('shift_jis', url_info.query_encoding)

    def test_not_http(self):
        url_info = URLInfo.parse('mailto:user@example.com')
        self.assertEqual('mailto:user@example.com', url_info.url)
        self.assertEqual('mailto', url_info.scheme)

    def test_url_info_invalids(self):
        self.assertRaises(ValueError, URLInfo.parse, '')
        self.assertRaises(ValueError, URLInfo.parse, '#')
        self.assertRaises(ValueError, URLInfo.parse, 'http://')
        self.assertRaises(ValueError, URLInfo.parse, 'example.com',
                          default_scheme=None)
        self.assertRaises(ValueError, URLInfo.parse, 'example....com')
        self.assertRaises(ValueError, URLInfo.parse, 'http://example....com')
        self.assertRaises(ValueError, URLInfo.parse, 'http://example…com')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[34.4kf]::4')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[34.4kf::4')
        self.assertRaises(ValueError, URLInfo.parse, 'http://dmn3]:3a:45')
        self.assertRaises(ValueError, URLInfo.parse, ':38/3')
        self.assertRaises(ValueError, URLInfo.parse, 'http://][a:@1]')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[[aa]]:4:]6')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[a]')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[a]')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[[a]')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[[a]]a]')
        self.assertRaises(ValueError, URLInfo.parse, 'http://[[a:a]]')
        self.assertRaises(ValueError, URLInfo.parse, 'http:///')
        self.assertRaises(ValueError, URLInfo.parse, 'http://?what?')
        self.assertRaises(ValueError, URLInfo.parse, 'http://#egg=wpull')
        self.assertRaises(ValueError, URLInfo.parse,
                          'http://:@example.com:?@/')
        self.assertRaises(ValueError, URLInfo.parse, 'http://\x00/')
        self.assertRaises(ValueError, URLInfo.parse, 'http://@@example.com/@')
        self.assertRaises(
            ValueError, URLInfo.parse,
            'http://ｆａｔ３２ｄｅｆｒａｇｍｅｎｔｅｒ.internets：：８０')
        self.assertRaises(
            ValueError, URLInfo.parse,
            'http://ｆａｔ３２ｄｅｆｒａｇｍｅｎｔｅｒ.internets：８０/')
        self.assertRaises(ValueError, URLInfo.parse, 'http:// /spaaaace')
        self.assertRaises(
            ValueError, URLInfo.parse,
            'http://a-long-long-time-ago-the-earth-was-ruled-by-dinosaurs-'
            'they-were-big-so-not-a-lot-of-people-went-around-hassling-them-'
            'actually-no-people-went-around-hassling-them-'
            'because-there-weren-t-any-people-yet-'
            'just-the-first-tiny-mammals-'
            'basically-life-was-good-'
            'lou-it-just-dont-get-no-better-than-this-'
            'yeah-'
            'then-something-happened-'
            'a-giant-meteorite-struck-the-earth-'
            'goodbye-dinosaurs-'
            'but-what-if-the-dinosaurs-werent-all-destroyed-'
            'what-if-the-impact-of-that-meteorite-created-a-parallel-dimension-'
            'where-the-dinosaurs-continue-to-thrive-'
            'and-evolved-into-intelligent-vicious-aggressive-beings-'
            'just-like-us-'
            'and-hey-what-if-they-found-their-way-back.movie'
        )
        self.assertRaises(
            ValueError, URLInfo.parse, 'http://[...]/python.xml%22')
        self.assertRaises(
            ValueError, URLInfo.parse, 'http://[…]/python.xml%22')
        self.assertRaises(
            ValueError, URLInfo.parse, 'http://[.]/python.xml%22')
        self.assertRaises(
            ValueError, URLInfo.parse,
            'http://wow:99999999999999999999999999999999999999999999999999999'
            '9999999999999999999999999999999999999999999999999999999999999999')
        self.assertRaises(
            ValueError, URLInfo.parse,
            'http://wow:-9999999999999999999999999999999999999999999999999999'
            '9999999999999999999999999999999999999999999999999999999999999999')

    def test_url_info_path_folding(self):
        self.parse_equal('http://example.com/.', 'http://example.com/')
        self.parse_equal('http://example.com/../', 'http://example.com/')
        self.parse_equal('http://example.com/../index.html',
                         'http://example.com/index.html')
        self.parse_equal('http://example.com/a/../../b/style.css',
                         'http://example.com/b/style.css')
        self.parse_equal('http://example.com/a/b/../style.css',
                         'http://example.com/a/style.css')

    def test_http_malformed_double_slash(self):
        self.parse_equal('http:example.com', 'http://example.com/')
        self.parse_equal('http:/example.com', 'http://example.com/')
        self.parse_equal('http:///example.com', 'http://example.com/')
        self.parse_equal('http:////example.com', 'http://example.com/')

    def test_url_info_reserved_char_is_ok(self):
        self.assertEqual(
            'http://example.com/@49IMG.DLL/$SESSION$/image.png;large',
            URLInfo.parse(
                'http://example.com/@49IMG.DLL/$SESSION$/image.png;large').url
        )
        self.assertEqual(
            'http://example.com/@49IMG.DLL/$SESSION$/imag%C3%A9.png;large',
            URLInfo.parse(
                'http://example.com/@49IMG.DLL/$SESSION$/imagé.png;large').url
        )
        self.assertEqual(
            'http://example.com/$c/%system.exe/',
            URLInfo.parse('http://example.com/$c/%system.exe/').url
        )

    def test_misleading_http_url(self):
        self.assertEqual(
            'http://example.com/'
            '?blah=http://example.com/?fail%3Dtrue',
            URLInfo.parse(
                'http://example.com/'
                '?blah=http://example.com/?fail%3Dtrue').url
        )
        # Check percent-encoded version of above
        self.assertEqual(
            'http://example.com/'
            '?blah=http%3A%2F%2Fexample.com%2F%3Ffail%3Dtrue',
            URLInfo.parse(
                'http://example.com/'
                '?blah=http%3A%2F%2Fexample.com%2F%3Ffail%3Dtrue').url
        )

    def test_url_info_misleading_parts(self):
        self.parse_equal('http://example.com?a', 'http://example.com/?a')
        self.parse_equal('http://example.com?a?', 'http://example.com/?a?')
        self.parse_equal('http://example.com#a', 'http://example.com/#a')
        self.parse_equal('http://example.com#a?', 'http://example.com/#a?')
        self.parse_equal('http://example.com?a#', 'http://example.com/?a')
        self.parse_equal('http://example.com/:10', 'http://example.com/:10')
        self.parse_equal('http://:@example.com?@/', 'http://example.com/?@/')

        # flatten paths will flatten consecutive slashes
        self.parse_equal('http://:@example.com/http://example.com',
                         'http://example.com/http:/example.com')

        self.parse_equal(
            'http://example.com/??blah=blah[0:]=bl%61h?blah"&d%26_',
            'http://example.com/??blah=blah[0:]=bl%61h?blah%22&d%26_'
        )

    def test_query_serialize_preservation(self):
        self.parse_equal(
            'http://example.com?a=',
            'http://example.com/?a='
        )
        self.parse_equal(
            'http://example.com?a=1',
            'http://example.com/?a=1'
        )
        self.parse_equal(
            'http://example.com?a=1&b',
            'http://example.com/?a=1&b'
        )
        self.parse_equal(
            'http://example.com?a=1&b=',
            'http://example.com/?a=1&b='
        )

    def test_ipv6_serialize_with_port(self):
        url_info = URLInfo.parse(
            'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:8080/ipv6'
        )

        self.assertEqual(
            'https://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:8080/ipv6',
            url_info.url
        )
        self.assertEqual(
            '[2001:db8:85a3:8d3:1319:8a2e:370:7348]:8080',
            url_info.host
        )

        # Default port
        url_info = URLInfo.parse(
            'http://[2001:db8:85a3:8d3:1319:8a2e:370:7348]/ipv6'
        )

        self.assertEqual(
            'http://[2001:db8:85a3:8d3:1319:8a2e:370:7348]/ipv6',
            url_info.url
        )
        self.assertEqual(
            '[2001:db8:85a3:8d3:1319:8a2e:370:7348]',
            url_info.host
        )

    def test_flatten_path_duplicate_slashes(self):
        self.parse_equal('http://example.com/a///b', 'http://example.com/a/b')

    def test_trailing_dot(self):
        self.parse_equal(
            'http://example.com./',
            'http://example.com./'
        )

        self.parse_equal(
            'http://example.com.:81/',
            'http://example.com.:81/'
        )

    def test_username_password(self):
        self.parse_equal(
            'http://UserName@example.com/',
            'http://UserName@example.com/'
        )
        self.parse_equal(
            'http://UserName:PassWord@example.com/',
            'http://UserName:PassWord@example.com/'
        )
        self.parse_equal(
            'http://:PassWord@example.com/',
            'http://:PassWord@example.com/'
        )
        self.parse_equal(
            'http://UserName:Pass:Word@example.com/',
            'http://UserName:Pass:Word@example.com/'
        )
        self.parse_equal(
            'http://User%40Name:Pass%3AWord@example.com/',
            'http://User%40Name:Pass:Word@example.com/'
        )
        self.parse_equal(
            'http://User Name%3A:@example.com/',
            'http://User%20Name%3A@example.com/'
        )

    def test_url_info_round_trip(self):
        urls = [
            'http://example.com/blah%20blah/',
            'example.com:81?blah=%c3%B0',
            'http://example.com/a/../../b/style.css',
            'http://example.com/'
            '?blah=http%3A%2F%2Fexample.com%2F%3Ffail%3Dtrue',
            'http://example.com/??blah=blah[0:]=bl%61h?blah"&d%26_',
            'http://[2001:db8:85a3:8d3:1319:8a2e:370:7348]/ipv6',
        ]

        for url in urls:
            parse_1 = URLInfo.parse(url).url
            parse_2 = URLInfo.parse(parse_1).url
            self.assertEqual(parse_1, parse_2)

    def test_ip_address_normalization(self):
        self.parse_equal(
            'http://0xC0.0x00.0x02.0xEB',
            'http://192.0.2.235/'
        )
        self.parse_equal(
            'http://0300.0000.0002.0353',
            'http://192.0.2.235/'
        )
        self.parse_equal(
            'http://0xC00002EB/',
            'http://192.0.2.235/'
        )
        self.parse_equal(
            'http://3221226219/',
            'http://192.0.2.235/'
        )
        self.parse_equal(
            'http://030000001353/',
            'http://192.0.2.235/'
        )
        self.parse_equal(
            'http://[2001:Db8:85a3:8d3:1319:8a2e:370:7348]:8080/ipv6',
            'http://[2001:db8:85a3:8d3:1319:8a2e:370:7348]:8080/ipv6'
        )
        self.parse_equal(
            'http://[0:0:0:0:0:0:0:1]',
            'http://[::1]/'
        )
        self.parse_equal(
            'http://[::ffff:192.0.2.128]/',
            'http://[::ffff:c000:280]/'
        )

    def test_setter(self):
        url_info = URLInfo('dummy')
        url_info.origin = 'Https:a:b@Example.com:8080'
        url_info.resource = '/a b?c d#e'

        self.assertEqual('https://a:b@example.com:8080/a%20b?c+d#e',
                         url_info.url)
