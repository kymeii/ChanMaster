# coding=utf-8
from dataclasses import dataclass

from trader.object import BarData

__author__ = "hanweiwei"
__date__ = "2019-06-02"


@dataclass
class ChanBarData(BarData):
    index: int = 0
    include_high: float = 0
    include_low: float = 0
    include_index: int = -1
    include_tail: int = -1

    def is_include(self):
        return self.include_index != -1

    def start_index(self):
        if self.is_include():
            return self.include_index
        else:
            return self.index

    def end_index(self):
        if self.is_include():
            return self.include_tail
        else:
            return self.index


@dataclass
class Fenxing(object):
    index: int = 0
    is_top: bool = False  # 是否顶分
    extreme_bar: ChanBarData = None
    bar_index: int = 0
    start_bar: ChanBarData = None
    end_bar: ChanBarData = None


@dataclass
class BasePen(object):
    def start_bar(self):
        raise NotImplementedError

    def end_bar(self):
        raise NotImplementedError

    def high(self):
        raise NotImplementedError

    def low(self):
        raise NotImplementedError


@dataclass
class Pen(BasePen):
    index: int
    start_fenxing: Fenxing
    end_fenxing: Fenxing
    is_rise: bool

    def start_bar(self):
        return self.start_fenxing.extreme_bar

    def start_bar_index(self):
        return self.start_fenxing.bar_index

    def end_bar(self):
        return self.end_fenxing.extreme_bar

    def end_bar_index(self):
        return self.end_fenxing.bar_index

    def high(self):
        if self.is_rise:
            return self.end_bar().include_high
        else:
            return self.start_bar().include_high

    def low(self):
        if self.is_rise:
            return self.start_bar().include_low
        else:
            return self.end_bar().include_low


@dataclass
class DerivePen(BasePen):
    index: int
    _start_bar: ChanBarData
    _end_bar: ChanBarData
    is_rise: bool = False

    def start_bar(self):
        return self._start_bar

    def end_bar(self):
        return self._end_bar

    def high(self):
        if self.is_rise:
            return self.end_bar().include_high
        else:
            return self.start_bar().include_high

    def low(self):
        if self.is_rise:
            return self.start_bar().include_low
        else:
            return self.end_bar().include_low


@dataclass
class Divider(object):
    """
    同级别分界线
    """
    last_pen: Pen
    confirm_pen: Pen


@dataclass
class Centre(object):
    """
    中枢
    """

    high: float  #  中枢上边界
    low: float  # 中枢下边界
    is_rise: bool  # 上涨中枢、下跌中枢
    start_pen: Pen  # 起笔
    end_pen: Pen  # 结束笔


@dataclass
class YanZhengFenxing(object):
    extreme_fenxing: Fenxing
    confirm_fenxing: Fenxing
    confirm_bar: ChanBarData
    loss_price: float
    invalid: bool = False  # 验证分型是否已经失效

    def should_stop_loss(self, bar: BarData):
        return self.extreme_fenxing.is_top and bar.close_price > self.loss_price \
               or \
               not self.extreme_fenxing.is_top and bar.close_price < self.loss_price
