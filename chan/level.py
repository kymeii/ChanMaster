# coding=utf-8
from trader.constant import Interval

__author__ = "hanweiwei"
__date__ = "2019-06-02"


class Level(object):

    def get_level(self):
        raise NotImplementedError

    def get_child_level(self):
        raise NotImplementedError

    def get_parent_level(self):
        raise NotImplementedError

    def get_grand_level(self):
        raise NotImplementedError


class ThirtyMinuteLevel(Level):
    """
    5分钟级别
    """

    def get_level(self):
        return Interval.MINUTE_30

    def get_child_level(self):
        return Interval.MINUTE_5

    def get_parent_level(self):
        return Interval.DAILY

    def get_grand_level(self):
        return Interval.DAILY


class FiveMinuteLevel(Level):
    """
    5分钟级别
    """

    def get_level(self):
        return Interval.MINUTE_5

    def get_child_level(self):
        return Interval.MINUTE

    def get_parent_level(self):
        return Interval.MINUTE_30

    def get_grand_level(self):
        return Interval.DAILY


class OneMinuteLevel(Level):

    def get_level(self):
        return Interval.MINUTE

    def get_child_level(self):
        return Interval.SECOND_10

    def get_parent_level(self):
        return Interval.MINUTE_5

    def get_grand_level(self):
        return Interval.MINUTE_30


def parse_level(level):
    if level == "5m":
        return FiveMinuteLevel()
    elif level == "1m":
        return OneMinuteLevel()
    elif level == "30m":
        return ThirtyMinuteLevel()
