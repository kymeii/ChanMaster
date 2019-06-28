# coding=utf-8
from typing import List

from chan.object import Fenxing, YanZhengFenxing, ChanBarData
from chan.trend import BaseTrend
from trader.object import BarData

__author__ = "hanweiwei"
__date__ = "2019-06-09"


class YanZhengFenxingHandler(object):
    """
    新产生一个极值点分型， 就有可能出多个验证分型
    """
    trend: BaseTrend = None
    extreme_fenxing: Fenxing = None
    confirm_fenxing: Fenxing = None  # 正在判定中的验证分型
    fenxing_pause: bool = False  # 是否分型停顿
    complete_yanzheng_fenxings: List[YanZhengFenxing] = []  # 已完成的验证分型
    judge_price: float = 0

    def on_new_fenxing(self, fenxing: Fenxing):
        if not self.extreme_fenxing and self.trend.pens[-1].end_fenxing.is_top!=fenxing.is_top:
            self.extreme_fenxing= fenxing
            return
        if fenxing.is_top != self.extreme_fenxing.is_top:
            return
        if fenxing.is_top and fenxing.extreme_bar.include_high > self.extreme_fenxing.extreme_bar.include_high:
            self.extreme_fenxing = fenxing
            self.confirm_fenxing = None
            self.fenxing_pause = False
        elif not fenxing.is_top and fenxing.extreme_bar.include_low < self.extreme_fenxing.extreme_bar.include_low:
            self.extreme_fenxing = fenxing
            self.confirm_fenxing = None
            self.fenxing_pause = False
        else:
            if self.complete_yanzheng_fenxings:
                last_yanzheng_fenxing = self.complete_yanzheng_fenxings[-1]
                if last_yanzheng_fenxing.extreme_fenxing == self.extreme_fenxing and not last_yanzheng_fenxing.invalid:
                    # 上一个验证分型未失效
                    return

            self.confirm_fenxing = fenxing
            if self.fenxing_pause:
                # 1.分型停顿 + 验证分型
                if self.confirm_fenxing.is_top:
                    loss_price = self.confirm_fenxing.extreme_bar.include_high
                else:
                    loss_price = self.confirm_fenxing.extreme_bar.include_low
                yanzheng_fenxing = YanZhengFenxing(extreme_fenxing=self.extreme_fenxing,
                                                   confirm_fenxing=self.confirm_fenxing, loss_price=loss_price,
                                                   confirm_bar=self.confirm_fenxing.end_bar)
                self.complete_yanzheng_fenxings.append(yanzheng_fenxing)
                self.trend.on_yanzheng_fenxing_success(yanzheng_fenxing)
                self.confirm_fenxing = None
            else:
                if self.extreme_fenxing.is_top:
                    extreme_fenxing_last_include_extreme_price = self.extreme_fenxing.end_bar.include_low
                else:
                    extreme_fenxing_last_include_extreme_price = self.extreme_fenxing.end_bar.include_high
                # 计算穿越判据价格
                if self.extreme_fenxing.is_top:
                    yanzheng_fenxing_last_include_extreme_price = self.confirm_fenxing.end_bar.include_low
                    if yanzheng_fenxing_last_include_extreme_price < extreme_fenxing_last_include_extreme_price:
                        self.judge_price = yanzheng_fenxing_last_include_extreme_price
                    else:
                        self.judge_price = extreme_fenxing_last_include_extreme_price
                else:
                    yanzheng_fenxing_last_include_extreme_price = self.confirm_fenxing.end_bar.include_high
                    if yanzheng_fenxing_last_include_extreme_price > extreme_fenxing_last_include_extreme_price:
                        self.judge_price = yanzheng_fenxing_last_include_extreme_price
                    else:
                        self.judge_price = extreme_fenxing_last_include_extreme_price

    def on_new_bar(self, bar: ChanBarData):
        if not self.extreme_fenxing:
            return
        # 验证分型破坏止损
        if self.complete_yanzheng_fenxings and not self.complete_yanzheng_fenxings[-1].invalid:
            last_yanzheng_fenxing = self.complete_yanzheng_fenxings[-1]
            if last_yanzheng_fenxing.should_stop_loss(bar):
                self.complete_yanzheng_fenxings[-1].invalid = True

        if self.confirm_fenxing:
            # 2。验证分型和极值分型极值穿越判断
            if self.extreme_fenxing.is_top and bar.close_price < self.judge_price \
                    or \
                    not self.extreme_fenxing.is_top and bar.close_price > self.judge_price:
                # 验证分型和极值分型极值穿越判据成立，验证分型有效
                if self.confirm_fenxing.is_top:
                    loss_price = self.confirm_fenxing.extreme_bar.include_high
                else:
                    loss_price = self.confirm_fenxing.extreme_bar.include_low
                yanzheng_fenxing = YanZhengFenxing(extreme_fenxing=self.extreme_fenxing,
                                                   confirm_fenxing=self.confirm_fenxing, loss_price=loss_price,
                                                   confirm_bar=bar)
                self.complete_yanzheng_fenxings.append(yanzheng_fenxing)
                self.trend.on_yanzheng_fenxing_success(yanzheng_fenxing)
                self.confirm_fenxing = None

        self.judge_fenxing_pause(bar)

    def judge_fenxing_pause(self, bar):
        if not self.fenxing_pause:
            # 分型停顿判断
            # 计算极值分型的最后一根k线的极值
            if self.extreme_fenxing.is_top:
                extreme_fenxing_last_include_extreme_price = self.extreme_fenxing.end_bar.include_low
            else:
                extreme_fenxing_last_include_extreme_price = self.extreme_fenxing.end_bar.include_high
            if self.extreme_fenxing.is_top and bar.close_price < extreme_fenxing_last_include_extreme_price \
                    or \
                    not self.extreme_fenxing.is_top and bar.close_price > extreme_fenxing_last_include_extreme_price:
                # 分型停顿确认是验证分型有效
                self.fenxing_pause = True

    def init(self, trend: BaseTrend):
        self.trend = trend
        last_pen = self.trend.pens[-1]
        if last_pen.end_fenxing.index + 1 >= len(self.trend.fenxings):
            return
        extreme_fenxing = trend.fenxings[last_pen.end_fenxing.index + 1]
        self.extreme_fenxing = extreme_fenxing
        for i in range(last_pen.end_fenxing.index + 1, len(trend.fenxings)):
            fenxing = trend.fenxings[i]
            if fenxing.is_top != self.extreme_fenxing.is_top:
                continue
            if fenxing.is_top and fenxing.extreme_bar.include_high > self.extreme_fenxing.extreme_bar.include_high:
                self.extreme_fenxing = fenxing
            elif not fenxing.is_top and fenxing.extreme_bar.include_low < self.extreme_fenxing.extreme_bar.include_low:
                self.extreme_fenxing = fenxing
        for i in range(self.extreme_fenxing.end_bar.index + 1, len(trend.bars)):
            self.judge_fenxing_pause(trend.bars[i])
