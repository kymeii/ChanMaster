# coding=utf-8
from abc import abstractmethod
from datetime import datetime
from typing import List

from chan.db.dao import ChanBarDataDao, CentreDao, PenDao
from chan.object import ChanBarData, Fenxing, Divider, Centre, Pen, YanZhengFenxing
from chan.sequence import SignatureSequenceItem
from trader.constant import Interval
from trader.object import BarData

__author__ = "hanweiwei"
__date__ = "2019-06-09"


class BaseTrend(object):
    """
    走势
    """

    def __init__(self, interval: Interval, parent_trend):
        """

        :param parentTrend:
        :type parentTrend:BaseTrend
        """
        self.interval = interval
        self.parent_trend: BaseTrend = parent_trend

        self.chan_bar_data_dao = ChanBarDataDao()
        self.pen_dao = PenDao()
        self.centre_dao = CentreDao()

        self.bars: List[ChanBarData] = []
        self.fenxings: List[Fenxing] = []
        self.pens: List[Pen] = []
        self.dividers: List[Divider] = []
        self.centres: List[Centre] = []

        # 当前是否上涨趋势
        self.is_rise = True

    def init_bars(self, bars: List[BarData]):
        for index, bar in enumerate(bars):
            # if index > len(bars) / 2:
            #     break
            self._append_bar(bar)

    def on_bar(self, bar: BarData):
        self._append_bar(bar)

    @abstractmethod
    def on_new_fenxing(self):
        pass

    @abstractmethod
    def on_new_pen(self):
        pass

    @abstractmethod
    def _on_derive_pen(self, start_datetime: datetime, end_datetime: datetime, is_rise: bool):

        """
        次级别推出本级别的笔
        :param pen:
        :return:
        """

    @abstractmethod
    def _handle_pens(self):
        pass

    def _append_bar(self, bar: BarData):
        index = len(self.bars)
        row = ChanBarData(symbol=bar.symbol, exchange=bar.exchange, interval=bar.interval, datetime=bar.datetime,
                          open_price=bar.open_price, high_price=bar.high_price, low_price=bar.low_price,
                          close_price=bar.close_price, volume=bar.volume, gateway_name=bar.gateway_name,
                          include_high=bar.high_price, include_low=bar.low_price,
                          include_index=-1, include_tail=-1, index=index)
        if len(self.bars) > 2:
            last_index = index - 1
            last_row = self.bars[last_index]
            if last_row.is_include():
                # 前一根K线也是包含, 找此包含关系的第一根K线的前一根K线
                last_last_row = self.bars[last_row.include_index - 1]
            else:
                last_last_row = self.bars[index - 2]
            before_include_after = (last_row.include_high >= row.high_price) and (
                    last_row.include_low <= row.low_price)
            after_include_before = (last_row.include_high <= row.high_price) and (
                    last_row.include_low >= row.low_price)
            if before_include_after:
                # 前包后
                if last_last_row.include_high > last_row.include_high:
                    # 低低
                    row.include_high = row.high_price
                    row.include_low = last_row.include_low
                else:
                    # 高高
                    row.include_high = last_row.include_high
                    row.include_low = row.low_price
                if last_row.is_include():
                    row.include_index = last_row.include_index
                else:
                    row.include_index = last_index
                    last_row.include_index = last_index
                for i in range(row.include_index, row.index):
                    self.bars[i].include_low = row.include_low
                    self.bars[i].include_high = row.include_high
            elif after_include_before:
                # 后包前
                if last_last_row.include_high > last_row.include_high:
                    # 低低
                    row.include_high = last_row.include_high
                    row.include_low = row.low_price
                else:
                    # 高高
                    row.include_high = row.high_price
                    row.include_low = last_row.include_low
                if last_row.is_include():
                    row.include_index = last_row.include_index
                else:
                    row.include_index = last_index
                    last_row.include_index = last_index
                for i in range(row.include_index, row.index):
                    self.bars[i].include_low = row.include_low
                    self.bars[i].include_high = row.include_high
            else:
                if last_row.is_include():
                    for i in range(last_index, last_row.include_index - 1, -1):
                        _temp_row = self.bars[i]
                        _temp_row.include_tail = last_index
        self.bars.append(row)
        self.chan_bar_data_dao.insert(row)
        self._handle_fenxing()

    def _handle_fenxing(self):
        index = len(self.bars) - 1
        cur = self.bars[len(self.bars) - 1]
        if cur.is_include():
            # 有包含关系，所以这跟k线不会产生新的分型
            return
        else:
            last_index = index - 1
        if last_index < 0:
            return
        last = self.bars[last_index]

        if last.is_include():
            # 取包含关系的第一根K线的前一根K线作为last
            last_last_index = last.include_index - 1
        else:
            last_last_index = last_index - 1
        if last_last_index < 0:
            return
        last_last = self.bars[last_last_index]

        if last_last.include_high > last.include_high and cur.include_high > last.include_high:
            # 底分型
            if last.is_include():
                for i in range(last.start_index(), last.end_index() + 1):
                    bar = self.bars[i]
                    if bar.low_price == bar.include_low:
                        extreme_bar = bar
            else:
                extreme_bar = last
            self.fenxings.append(
                Fenxing(index=len(self.fenxings), is_top=False, extreme_bar=extreme_bar, bar_index=extreme_bar.index,
                        start_bar=last_last, end_bar=cur))
        elif last_last.include_high < last.include_high and cur.include_high < last.include_high:
            # 顶分型
            if last.is_include():
                for i in range(last.start_index(), last.end_index() + 1):
                    bar = self.bars[i]
                    if bar.high_price == bar.include_high:
                        extreme_bar = bar
            else:
                extreme_bar = last
            self.fenxings.append(
                Fenxing(index=len(self.fenxings), is_top=True, extreme_bar=extreme_bar, bar_index=extreme_bar.index,
                        start_bar=last_last, end_bar=cur))
        else:
            # 有新的分型产生，才会产生新的笔
            return
        self._handle_pens()
        self.on_new_fenxing()

    def _handle_segments(self, has_fix_pen=False):
        """
        线段
        :return:
        """
        if len(self.pens) < 3: return

        if has_fix_pen:
            while self.dividers:
                divider = self.dividers[-1]
                if self.pens[-1].index <= divider.confirm_pen.index:
                    # 修正笔导致之前的线段划分失效
                    self.dividers.remove(divider)
                    continue
                break

        if self.dividers:
            divider = self.dividers[-1]
            # 为什么直接+4： 因为确认前一个同级别分界线时，新的线段至少已经走了三笔，可以直接从第四笔取特征序列来进行后续的判断
            signature_sequence_index = divider.confirm_pen.index + 1
            if signature_sequence_index >= len(self.pens):
                return
            start_pen = self.pens[divider.last_pen.index + 1]

        else:
            signature_sequence_index = 0  # 当前特征序列在pens列表中的索引
            current_pen = self.pens[signature_sequence_index]

            # 始终把初始走势当成上涨线段
            # 第一笔下跌，这一笔是特征序列的0号
            # 第一笔上涨，就把第二笔当作特征序列的0号，不管第一笔
            if current_pen.is_rise:
                # 第一笔上涨，就把第二笔当作特征序列的0号，不管第一笔
                # 第一笔就是线段的开始
                signature_sequence_index += 1
                start_pen = self.pens[0]
            else:
                # 第一笔下跌，把第二笔作为线段的开始
                start_pen = self.pens[signature_sequence_index + 1]
        current_pen = self.pens[signature_sequence_index]
        # print(current_pen.index)
        current_signature = SignatureSequenceItem.create_by_pen(current_pen)
        signature_sequence_index += 2
        while signature_sequence_index < len(self.pens):
            next_signature = SignatureSequenceItem.create_by_pen(self.pens[signature_sequence_index])
            relation, ret_signature = current_signature.grow(next_signature)
            if self.interval == Interval.MINUTE_5:
                print(current_signature.extremum_pen_index, current_signature.high, current_signature.low,
                      next_signature.extremum_pen_index,
                      next_signature.high, next_signature.low, relation,
                      ret_signature.extremum_pen_index)
            if relation == SignatureSequenceItem.EXTEND:
                # 线段的延伸
                current_signature = ret_signature
                signature_sequence_index += 2
            elif ret_signature == SignatureSequenceItem.INCLUDE:
                current_signature = ret_signature
                signature_sequence_index += 2
            else:
                # 线段的转折
                pen = self.pens[ret_signature.extremum_pen_index]
                divider = Divider(self.pens[pen.index - 1], confirm_pen=self.pens[signature_sequence_index])
                self.dividers.append(divider)

                # 推笔
                if self.parent_trend:
                    self.parent_trend._on_derive_pen(start_pen.start_bar().datetime,
                                                     divider.last_pen.end_bar().datetime,
                                                     ret_signature.is_rise)
                signature_sequence_index += 1
                if signature_sequence_index >= len(self.pens):
                    break
                start_pen = self.pens[divider.last_pen.index + 1]
                current_signature = SignatureSequenceItem.create_by_pen(self.pens[signature_sequence_index])  # 特征序列的1号
                signature_sequence_index += 2

    def _handle_centre(self):
        """
        处理中枢
        :return:
        """
        if len(self.pens) < 3:
            return
        if self.centres:
            cur_centre = self.centres[-1]
            cur_pen = self.pens[-1]
            if cur_pen.index - cur_centre.end_pen.index == 1:
                if not (cur_pen.high() < cur_centre.low or cur_pen.low() > cur_centre.high):
                    # 中枢维持
                    cur_centre.end_pen = cur_pen
                    self.centre_dao.insert(cur_centre)
                    return
                else:
                    # 中枢破坏
                    return
            elif cur_pen.index <= cur_centre.end_pen.index:
                # 没有产生新的笔，是修正笔
                # 最简单就是把这个中枢删掉，重新生成个中枢。 麻烦点，就去删掉之前中枢中的笔，重新确定中枢的属性。
                # 这里采用简单的方法
                self.centres.remove(cur_centre)

        # 新中枢判断
        if self.centres:
            cur_pen = self.pens[self.centres[-1].end_pen.index + 1]  # 这个笔是出三买和三卖的笔
        else:
            cur_pen = self.pens[0]
            if cur_pen.is_rise:
                cur_pen = self.pens[1]

        new_centre = None
        cur_index = cur_pen.index
        next_index = cur_pen.index + 2
        while next_index < len(self.pens):
            cur_pen = self.pens[cur_index]
            next_pen = self.pens[next_index]
            if not (cur_pen.high() < next_pen.low() or cur_pen.low() > next_pen.high()):
                centre_low = cur_pen.low() if cur_pen.low() > next_pen.low() else next_pen.low()
                centre_high = cur_pen.high() if cur_pen.high() < next_pen.high() else next_pen.high()
                new_centre = Centre(high=centre_high, low=centre_low, is_rise=not cur_pen.is_rise, start_pen=cur_pen,
                                    end_pen=next_pen)
                self.centres.append(new_centre)
                self.centre_dao.insert(new_centre)
                break
            cur_index += 2
            next_index += 2

        # 产生了新中枢，去看中枢是否延伸
        if not new_centre:
            return
        cur_index = next_index + 1
        while cur_index < len(self.pens):
            cur_pen = self.pens[cur_index]
            if not (cur_pen.high() < new_centre.low or cur_pen.low() > new_centre.high):
                # 中枢维持
                new_centre.end_pen = cur_pen
                self.centre_dao.insert(new_centre)
                cur_index += 1
                continue
            break

    def on_yanzheng_fenxing_success(self, yanzheng_fenxing: YanZhengFenxing):
        pass
