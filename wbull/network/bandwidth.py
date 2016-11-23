"""Bandwidth Measurement.

This module provides classes for measuring data transfer speed
and speed limiting.
"""
import collections

import time

from typing import Optional


BandwidthSample = collections.namedtuple(
    'BandwidthSample', ['time_difference', 'bytes_transferred']
)


class BandwidthMeter:
    def __init__(self, sample_size: int=20, sample_min_time: float=0.15,
                 stall_time: float=5.0):
        """Calculates the speed of data transfer.

        Args:
            sample_size: The number of samples for measuring the speed.
            sample_min_time: The minimum duration between samples in
                seconds.
            stall_time: The time in seconds to consider no traffic
                to be connection stalled.
        """
        self._samples = collections.deque(maxlen=sample_size)
        self._sample_min_time = sample_min_time
        self._stall_time = stall_time
        self._last_feed_time = None
        self._collected_bytes_transferred = 0

    def stalled(self, current_time: Optional[float]=None) -> bool:
        """Return whether the connection is stalled."""
        if self._samples:
            return (current_time or time.monotonic()) - self._last_feed_time >= self._stall_time
        else:
            return False

    @property
    def collected_sample_count(self) -> int:
        """Return the number of samples collected."""
        return len(self._samples)

    def feed(self, data_len: int, feed_time: Optional[float]=None):
        """Update the bandwidth meter.

        Args:
            data_len: The number of bytes transferred since the last
                call this function.
            feed_time: A timestamp in seconds.
        """
        assert data_len >= 0, 'Cannot be negative: {}'.format(data_len)
        if not data_len:
            return

        time_now = feed_time or time.monotonic()

        if self._last_feed_time:
            time_diff = time_now - self._last_feed_time

            if time_diff < self._sample_min_time:
                return
        else:
            self._last_feed_time = time_now
            return

        self._collected_bytes_transferred += data_len
        self._last_feed_time = time_now

        self._samples.append(BandwidthSample(
            time_diff, self._collected_bytes_transferred
        ))

        self._collected_bytes_transferred = 0

    def speed(self) -> float:
        """Return the current transfer speed.

        Returns:
            The speed in bytes per second.
        """
        if self._samples:
            time_sum, data_len_sum = map(sum, zip(*self._samples))

            if time_sum:
                return data_len_sum / time_sum

        return 0


class BandwidthLimiter(BandwidthMeter):
    def __init__(self, rate_limit: float=0):
        """Calculates time to limit bandwidth speeds.

        Args:
            rate_limit: Speed in bytes per second.
        """
        super().__init__(sample_min_time=0)
        self._rate_limit = rate_limit

    @property
    def rate_limit(self) -> float:
        """Return the rate limit in bytes per second."""
        return self._rate_limit

    @rate_limit.setter
    def rate_limit(self, new_limit: float):
        self._rate_limit = new_limit

    def sleep_time(self) -> float:
        """Return the time needed to sleep to not exceed the rate limit."""
        if not self._samples or not self._rate_limit:
            return 0

        elapsed_time, byte_sum = map(sum, zip(*self._samples))

        expected_elapsed_time = byte_sum / self._rate_limit

        if expected_elapsed_time > elapsed_time:
            sleep_time = expected_elapsed_time - elapsed_time
            return sleep_time
        else:
            return 0

