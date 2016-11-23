import unittest
from urllib.parse import urljoin

from wbull.format.url.path import flatten_path, is_subdir


class URLPathTestCase(unittest.TestCase):
    def test_is_subdir(self):
        # Test filename strip
        self.assertTrue(is_subdir('blog/', 'blog/index.html'))
        self.assertTrue(is_subdir('blog/', 'blog/album/index.html'))

        # Test empty path
        self.assertTrue(is_subdir('', ''))
        self.assertTrue(is_subdir('a', 'a'))
        self.assertTrue(is_subdir('/', '/'))

        # Test subdir paths
        self.assertTrue(is_subdir('blog/', 'blog/'))
        self.assertTrue(is_subdir('blog/', 'blog/album/'))
        self.assertTrue(is_subdir('blog/', 'blog/album/new/'))
        self.assertTrue(is_subdir('blog/album/', 'blog/album/new/'))
        self.assertFalse(is_subdir('blog/album/', 'blog/tags/album/'))
        self.assertFalse(is_subdir('blog/album/new/', 'blog/'))
        self.assertFalse(is_subdir('blog/pic/', 'blog/pictures/'))

        # Test leading slash
        self.assertTrue(is_subdir('/blog/', '/blog/'))
        self.assertTrue(is_subdir('/blog/', '/blog/album/'))

        # Test glob
        self.assertTrue(
            is_subdir('a/b/', 'a/b/c/', wildcards=True)
        )
        self.assertFalse(
            is_subdir('a/b/c/', 'a/b/', wildcards=True)
        )
        self.assertTrue(
            is_subdir('album/200?/', 'album/2005/06/', wildcards=True)
        )
        self.assertFalse(
            is_subdir('a/200?/', 'album/1995/08/', wildcards=True)
        )

    def test_flatten_path(self):
        # Check identity
        self.assertEqual('', flatten_path(''))
        self.assertEqual('/', flatten_path('/'))

        # Check dot segment beyond root
        self.assertEqual('', flatten_path('.'))
        self.assertEqual('', flatten_path('..'))
        self.assertEqual('', flatten_path('./'))
        self.assertEqual('', flatten_path('../'))
        self.assertEqual('', flatten_path('/.'))
        self.assertEqual('', flatten_path('/..'))
        self.assertEqual('', flatten_path('./.'))
        self.assertEqual('', flatten_path('../../../'))
        self.assertEqual('', flatten_path('.././'))

        # Check identity with slash
        self.assertEqual('dog/cat', flatten_path('dog/cat'))
        self.assertEqual('dog/cat/', flatten_path('dog/cat/'))
        self.assertEqual('dog/cat//', flatten_path('dog/cat//'))
        self.assertEqual('dog//cat', flatten_path('dog//cat'))

        # Check dot segment
        self.assertEqual('dog', flatten_path('dog/.'))
        self.assertEqual('dog', flatten_path('dog/cat/..'))
        self.assertEqual('dog/', flatten_path('dog/./'))
        self.assertEqual('dog/', flatten_path('dog/cat/../'))
        self.assertEqual('dog/bird', flatten_path('dog/cat/../bird'))
        self.assertEqual('dog/bird/', flatten_path('dog/cat/../bird/'))
        self.assertEqual(
            'dog//bird.html',
            flatten_path('dog/../dog/.//cat/.././bird.html')
        )

        # Check leading slash preservation
        self.assertEqual('/', flatten_path('/'))
        self.assertEqual('//', flatten_path('//'))
        self.assertEqual('///a', flatten_path('///a'))
        self.assertEqual('///a', flatten_path('///a'))
        self.assertEqual('///a/c', flatten_path('///a/b/../c'))

        # Check parent multiple slashes
        self.assertEqual('a//b', flatten_path('a////../../b'))

    def test_flatten_path_slash_removal(self):
        # Check identity
        self.assertEqual('', flatten_path('', flatten_slashes=True))

        # Check dot segment beyond root
        self.assertEqual('', flatten_path('../..//../', flatten_slashes=True))

        # Check removal
        self.assertEqual(
            'a/b/c/d/',
            flatten_path('a//b///c////d/////', flatten_slashes=True)
        )

        # Check path traversal
        self.assertEqual(
            'a/c/d',
            flatten_path('a//b//../../c//d', flatten_slashes=True)
        )

    def test_url_join(self):
        self.assertEqual(
            'http://example.net',
            urljoin('http://example.com', '//example.net')
        )
        self.assertEqual(
            'https://example.net',
            urljoin('https://example.com', '//example.net')
        )
        self.assertEqual(
            'http://example.net',
            urljoin('http://example.com/', '//example.net')
        )
        self.assertEqual(
            'https://example.net',
            urljoin('https://example.com/', '//example.net')
        )
        self.assertEqual(
            'http://example.net/',
            urljoin('http://example.com/', '//example.net/')
        )
        self.assertEqual(
            'https://example.net/',
            urljoin('https://example.com/', '//example.net/')
        )
        self.assertEqual(
            'https://example.com/asdf',
            urljoin('https://example.com/cookies', '/asdf')
        )
        self.assertEqual(
            'http://example.com/asdf',
            urljoin('http://example.com/cookies', 'asdf')
        )
        self.assertEqual(
            'http://example.com/cookies/asdf',
            urljoin('http://example.com/cookies/', 'asdf')
        )
        self.assertEqual(
            'https://example.net/asdf',
            urljoin('https://example.net/', '/asdf')
        )
        self.assertEqual(
            'http://example.net/asdf',
            urljoin('https://example.com', 'http://example.net/asdf')
        )
        self.assertEqual(
            'http://example.com/',
            urljoin('http://example.com', '//example.com/')
        )
        self.assertEqual(
            'http://example.com/',
            urljoin('http://example.com/', '//')
        )
        self.assertEqual(
            'http://example.com/',
            urljoin('http://example.com/', '///')
        )
        self.assertEqual(
            'http://example.com/a/style.css',
            urljoin('http://example.com/a/', './style.css')
        )
        self.assertEqual(
            'http://example.com/style.css',
            urljoin('http://example.com/a/', './../style.css')
        )
