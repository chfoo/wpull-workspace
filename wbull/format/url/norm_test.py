import unittest

from wbull.format.url.norm import normalize_hostname, normalize_path, \
    normalize_query, normalize_fragment, \
    normalize_username, normalize_password


class URLNormTestCase(unittest.TestCase):
    def test_normalize_hostname(self):
        self.assertEqual('example.com', normalize_hostname('Example.Com'))
        self.assertEqual('localhost', normalize_hostname('LocalHost'))
        self.assertEqual('www.xn--hda.com', normalize_hostname('www.ð.com'))
        self.assertEqual('www.xn--hda.com', normalize_hostname('www.ð.com'))
        self.assertEqual('www.xn--e-oga.com', normalize_hostname('www.ðe.com'))

        with self.assertRaises(ValueError):
            normalize_hostname('example…com')

        with self.assertRaises(ValueError):
            normalize_hostname(
                'a-long-long-time-ago-the-earth-was-ruled-by-dinosaurs-'
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

    def test_normalize_path(self):
        self.assertEqual('/%C3%B6_%20_%C3%B0/', normalize_path('/%c3%b6_ _ð/'))

    def test_normalize_query(self):
        self.assertEqual(
            '%C3%B6=+%23&_=%C3%B0', normalize_query('%c3%b6= #&_=ð')
        )

    def test_normalize_fragment(self):
        self.assertEqual(
            '%C3%B6_%20_%C3%B0_%60', normalize_fragment('%c3%b6_ _ð_`')
        )

    def test_normalize_username(self):
        self.assertEqual(
            '%C3%B6_%3A%20_%C3%B0_%40', normalize_username('%c3%b6_: _ð_@')
        )

    def test_normalize_password(self):
        self.assertEqual(
            '%C3%B6_:%20_%C3%B0_%40', normalize_password('%c3%b6_: _ð_@')
        )


