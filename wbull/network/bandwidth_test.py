import unittest

from wbull.network.bandwidth import BandwidthMeter, BandwidthLimiter


class TestBandwidthMeter(unittest.TestCase):
    def test_feed_meter(self):
        meter = BandwidthMeter()
        self.assertEqual(0, meter.collected_sample_count)
        self.assertEqual(0, meter.speed())

        meter.feed(100, feed_time=1)

        self.assertEqual(0, meter.collected_sample_count)
        self.assertEqual(0, meter.speed())

        meter.feed(150, feed_time=2)

        self.assertEqual(1, meter.collected_sample_count)
        self.assertEqual(150, meter.speed())

        meter.feed(175, feed_time=3)

        self.assertEqual(2, meter.collected_sample_count)
        self.assertEqual(162.5, meter.speed())

    def test_meter_stalled(self):
        meter = BandwidthMeter()

        self.assertFalse(meter.stalled())

        meter.feed(100, feed_time=1)
        meter.feed(100, feed_time=2)

        self.assertFalse(meter.stalled(current_time=3))
        self.assertTrue(meter.stalled(current_time=10))

    def test_feed_empty(self):
        meter = BandwidthMeter()
        meter.feed(0, feed_time=1)

        self.assertEqual(0, meter.collected_sample_count)
        self.assertEqual(0, meter.speed())

    def test_feed_below_sample_time(self):
        meter = BandwidthMeter(sample_min_time=1)
        meter.feed(1, feed_time=0.5)

        self.assertEqual(0, meter.speed())

        meter.feed(1, feed_time=0.6)

        self.assertEqual(0, meter.speed())


class TestBandwidthLimiter(unittest.TestCase):
    def test_limiter(self):
        limiter = BandwidthLimiter(123456)
        limiter.rate_limit = 10
        self.assertEqual(10, limiter.rate_limit)

        limiter.feed(20, feed_time=1)

        self.assertEqual(0, limiter.sleep_time())

        limiter.feed(25, feed_time=2)

        self.assertEqual(1.5, limiter.sleep_time())

        limiter.feed(5, feed_time=3.5)

        self.assertEqual(0.5, limiter.sleep_time())

        limiter.feed(1, feed_time=10)

        self.assertEqual(0, limiter.sleep_time())

