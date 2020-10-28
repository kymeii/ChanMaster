# coding=utf-8
from datetime import datetime
from typing import List

from chan.level import Level
from chan.object import ChanBarData, Pen, YanZhengFenxing, DerivePen
from chan.trend import BaseTrend
from chan.yanzheng_fenxing_handler import YanZhengFenxingHandler
from event.engine import EventEngine, Event
from tools import time_tools
from trader.constant import Exchange, Interval
from trader.event import EVENT_BAR
from trader.gateway import BaseGateway
from trader.object import KLineRequest, BarData, SubscribeBarRequest

__author__ = "hanweiwei"
__date__ = "2018/10/25"


class SubTrend(BaseTrend):
    def __init__(self, interval: Interval, parent_trend):
        super().__init__(interval, parent_trend)

    def _handle_pens(self):
        if len(self.pens):
            cur = self.pens[-1]
            last_fenxing = cur.end_fenxing
        elif len(self.fenxings) > 2:
            last_fenxing = self.fenxings[0]
        else:
            # 分型不够
            return
        index = last_fenxing.index + 1
        while index < len(self.fenxings):

            cur_fenxing = self.fenxings[index]
            if last_fenxing.is_top == cur_fenxing.is_top:
                # 同向分型 ,看是否需要修正笔
                if last_fenxing.is_top and cur_fenxing.extreme_bar.include_high > last_fenxing.extreme_bar.include_high \
                        or \
                        not last_fenxing.is_top and cur_fenxing.extreme_bar.include_low < last_fenxing.extreme_bar.include_low:
                    self._fix_pen()
                    # 修正笔，重置last_fenxing
                    if len(self.pens):
                        cur = self.pens[-1]
                        last_fenxing = cur.end_fenxing
                    elif last_fenxing.index + 1 < len(self.fenxings):
                        last_fenxing = self.fenxings[last_fenxing.index + 1]
                    else:
                        # 分型不够
                        return
                    index = last_fenxing.index + 1
                    continue

            if self._is_fenxing_match(last_fenxing.index, cur_fenxing.index):
                pen = Pen(len(self.pens), last_fenxing, cur_fenxing, cur_fenxing.is_top)
                self.pens.append(pen)
                # print("new pen %s -> %s", pen.start_bar_index(), pen.end_bar_index())
                self.pen_dao.insert(pen)
                self._handle_segments(False)
                self._handle_centre()
                # 新的笔产生，重置last_fenxing
                last_fenxing = cur_fenxing
            index = cur_fenxing.index + 1

    def _fix_pen(self):
        while self.pens:
            # 修正笔
            last_pen = self.pens[-1]
            for i in range(last_pen.end_fenxing.index + 1, len(self.fenxings)):
                if self._is_fenxing_match(last_pen.start_fenxing.index, i):
                    last_pen_end_bar_index_before = last_pen.end_bar_index()
                    last_pen.end_fenxing = self.fenxings[i]
                    self.pen_dao.insert(self.pens[-1])
                    # print("fix pen %s %s,%s -> %s,%s" % (last_pen.index,
                    #                                      self.pens[-1].start_bar_index(), last_pen_end_bar_index_before,
                    #                                      self.pens[-1].start_bar_index(),
                    #                                      self.pens[-1].end_bar_index()))
                    self._handle_segments(True)
                    self._handle_centre()
                    return True

            # print("delete pen", last_pen.index, last_pen.start_bar_index(), last_pen.end_bar_index())
            self.pens.remove(last_pen)
            self.pen_dao.delete(last_pen)
        return False

    def _is_fenxing_match(self, start: int, end: int):

        # if end - start == 1:
        #     # 次级别要有结构
        #     return False
        start_fenxing = self.fenxings[start]
        end_fenxing = self.fenxings[end]

        # 满足5根k线否
        start_fenxing_end_bar_index = self.bars[start_fenxing.extreme_bar.end_index() + 1].end_index()
        end_fenxing_start_bar_index = self.bars[end_fenxing.extreme_bar.start_index() - 1].start_index()
        if end_fenxing_start_bar_index - start_fenxing_end_bar_index < 2:
            # 不满足5根k线
            return False

        # end 是不是start分型与end分型之间的极值分型
        # 找出极值分型, 以及回荡深度，为次高点成笔做准备
        highest = start_fenxing.extreme_bar.include_high  # 记录遍利过的最高点
        lowest = start_fenxing.extreme_bar.include_low  # 记录遍历过的最低点
        highest_fenxing = start_fenxing
        lowest_fenxing = start_fenxing

        secondary_back_deep = 0  # 次高点成笔回荡深度
        for i in range(start + 1, end + 1):
            cur = self.fenxings[i]
            if cur.is_top == start_fenxing.is_top and secondary_back_deep < 0.5:
                if start_fenxing.is_top:
                    secondary_back_deep = (cur.extreme_bar.include_high - lowest) / (highest - lowest)
                else:
                    secondary_back_deep = (highest - cur.extreme_bar.include_low) / (highest - lowest)

            if cur.is_top and highest < cur.extreme_bar.include_high:
                highest = cur.extreme_bar.include_high
                highest_fenxing = cur
            elif not cur.is_top and lowest > cur.extreme_bar.include_low:
                lowest = cur.extreme_bar.include_low
                lowest_fenxing = cur

        if start_fenxing.is_top and highest_fenxing != start_fenxing \
                or \
                not start_fenxing.is_top and lowest_fenxing != start_fenxing:
            return False

        # end分型是极值分型，可以直接成笔
        if start_fenxing.is_top and lowest_fenxing == end_fenxing \
                or \
                not start_fenxing.is_top and highest_fenxing == end_fenxing:
            return True

        # 回荡深度超过50%，不满足次高点成笔
        if secondary_back_deep > 0:
            return False
        # 次高点成笔，满足4根k线否
        if start_fenxing.is_top:
            extreme_fenxing = lowest_fenxing
        else:
            extreme_fenxing = highest_fenxing
        extreme_fenxing_start_bar_index = self.bars[extreme_fenxing.bar_index - 1].include_index
        if extreme_fenxing_start_bar_index - start_fenxing_end_bar_index < 1:
            # 次高点成笔不足4根k线
            return True
        else:
            # 次高点成笔
            return True


class Trend(BaseTrend):
    def __init__(self, interval: Interval, parent_trend):
        super().__init__(interval, parent_trend)
        self.pens: List[Pen] = []
        self.bars: List[ChanBarData] = []
        self.yanzheng_fenxing_handler: YanZhengFenxingHandler = None

    def _on_derive_pen(self, start_datetime: datetime, end_datetime: datetime, is_rise: bool):
        # 需要修正，推笔不能用分型来表示，应该严格定义到那根K线上
        if self.interval == Interval.MINUTE_5:
            start_datetime = time_tools.m1_2_m5(start_datetime)
            end_datetime = time_tools.m1_2_m5(end_datetime)
        elif self.interval == Interval.MINUTE_30:
            print("30m pend %s %s" % (start_datetime, end_datetime))
            start_datetime = time_tools.m5_2_m30(start_datetime)
            end_datetime = time_tools.m5_2_m30(end_datetime)
            print("30m pend %s %s" % (start_datetime, end_datetime))

        start_bar = None
        end_bar = None
        for i in range(len(self.bars) - 1, -1, -1):
            bar = self.bars[i]
            if bar.datetime < start_datetime:
                break
            if bar.datetime == end_datetime:
                end_bar = bar
            if bar.datetime == start_datetime:
                start_bar = bar
        if start_bar and end_bar:
            pen = DerivePen(index=len(self.pens), _start_bar=start_bar, _end_bar=end_bar,
                            is_rise=is_rise)
            self.pens.append(pen)
            self.pen_dao.insert(pen)
            self._handle_segments(False)
            self.on_new_pen()
        else:
            # print(start_datetime, end_datetime)
            pass
        self._handle_centre()

    def on_bar(self, bar: BarData):
        super(Trend, self).on_bar(bar)
        if self.yanzheng_fenxing_handler:
            self.yanzheng_fenxing_handler.on_new_bar(self.bars[-1])

    def on_new_fenxing(self):
        if self.yanzheng_fenxing_handler:
            self.yanzheng_fenxing_handler.on_new_fenxing(self.fenxings[-1])

    def on_new_pen(self):
        # 验证分型处理器更新
        self.yanzheng_fenxing_handler = YanZhengFenxingHandler()
        # self.yanzheng_fenxing_handler.init(self)

    def on_yanzheng_fenxing_success(self, yanzheng_fenxing: YanZhengFenxing):
        last_pen = self.pens[-1]
        if yanzheng_fenxing.extreme_fenxing.is_top and yanzheng_fenxing.extreme_fenxing.extreme_bar.include_high > last_pen.high():
            print("二卖", yanzheng_fenxing.confirm_bar.index, "开仓价", yanzheng_fenxing.confirm_bar.close_price,
                  "止损价", yanzheng_fenxing.loss_price)
        elif not yanzheng_fenxing.extreme_fenxing.is_top and yanzheng_fenxing.extreme_fenxing.extreme_bar.include_low > last_pen.low():
            print("二买", yanzheng_fenxing.confirm_bar.index, "开仓价", yanzheng_fenxing.confirm_bar.close_price,
                  "止损价", yanzheng_fenxing.loss_price)


class ChanApp(object):
    """
    做本级别线段
    使用次级别严格笔，推出本级别笔，再推出本级别的中枢和线段
    """

    def __init__(self, level: Level, gateway: type, exchange: Exchange, symbol: str):
        """

        :param level:
        :param gateway:
        :param exchange:
        :param symbol:
        """
        self._level = level
        self._exchange = exchange
        self._symbol = symbol
        self._parent_trend = Trend(self._level.get_parent_level(), None)
        self._trend = Trend(self._level.get_level(), self._parent_trend)
        self._child_trend = SubTrend(self._level.get_child_level(), self._trend)
        self._event_engine = EventEngine()
        self._gateway: BaseGateway = gateway(self._event_engine)

    def init(self):
        init_start_time = time_tools.timestamp()

        sub_klines = 8000
        request = KLineRequest(self._symbol, self._exchange, self._level.get_parent_level(), int(sub_klines / 5 / 5))
        bars = self._gateway.get_kline_data(request)
        self._parent_trend.init_bars(bars)

        request = KLineRequest(self._symbol, self._exchange, self._level.get_level(), int(sub_klines / 5))
        bars = self._gateway.get_kline_data(request)
        self._trend.init_bars(bars)

        request = KLineRequest(self._symbol, self._exchange, self._level.get_child_level(), sub_klines)
        bars = self._gateway.get_kline_data(request)
        self._child_trend.init_bars(bars)
        init_end_time = time_tools.timestamp()
        print("init total time %s" % (init_end_time - init_start_time))

    def start(self):
        self.init()

        print("init bar finish")
        self._event_engine.register(EVENT_BAR, self.on_bar)
        self._event_engine.start()

        self._gateway.subscribe_bar(
            SubscribeBarRequest(symbol=self._symbol, exchange=self._exchange, interval=self._level.get_child_level()))

        self._gateway.subscribe_bar(
            SubscribeBarRequest(symbol=self._symbol, exchange=self._exchange, interval=self._level.get_level()))

        self._gateway.subscribe_bar(
            SubscribeBarRequest(symbol=self._symbol, exchange=self._exchange, interval=self._level.get_parent_level()))
        self._gateway.connect(None)

    def on_bar(self, event: Event):
        bar: BarData = event.data
        # print(bar)
        if bar.interval == self._level.get_level():
            self._trend.on_bar(bar)
        elif bar.interval == self._level.get_child_level():
            self._child_trend.on_bar(bar)
        elif bar.interval == self._level.get_parent_level():
            self._parent_trend.on_bar(bar)

# dataframe_60 = getKLineData("600887.SS", scale=MINUTE_60, start_date="20181010", end_date="20181118")
# dataframe_60 = getKLineData("SH603019", scale=MINUTE_60, count=len(dataframe) / 12)
# handle_include(dataframe_60)
# handle_fenxing(dataframe_60)
# pens_60 = handle_pen(dataframe_60)
# if pens_60:
#     print dataframe_60.ix[pens_60[0]["start"]]

# app_log.info("处理数据完毕：%s", datetime.datetime.now())
#
# json_str = dataframe.to_json(orient="records")
# data = encoder.loads(json_str)
# data = {"kline": data, "pens": pens}
# with open("../static/data.encoder", "w") as fp:
#     encoder.dump(data, fp)
#     fp.close()
# # break
# time.sleep(60)

# plt.figure()
# pl = dataframe.plot.box()
# plt.show()
