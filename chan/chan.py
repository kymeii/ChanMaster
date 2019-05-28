# coding=utf-8
import time
import json
# from yahoo.api import getKLineData, MINUTE_60, MINUTE_5, MINUTE_1
import os

import datetime

from app import app_log
from sina.api import getKLineData, MINUTE_5, MINUTE_30, MINUTE_60, DAY
from pandas import DataFrame
import matplotlib.pyplot as plt

__author__ = "hanweiwei"
__date__ = "2018/10/25"

STRICT_PEN = 1
DERIVATION_PEN = 2
PEN_TYPE = STRICT_PEN


def handle_include(dataframe):
    """

    :param dataframe:
    :type dataframe:DataFrame
    :return:
    """
    dataframe["includeIndex"] = -1  # 一组包含关系的第一根K线索引
    dataframe["includeHigh"] = 0
    dataframe["includeLow"] = 0
    dataframe["includeTail"] = 0

    include_index = list(dataframe.columns).index('includeIndex')
    includeHigh_index = list(dataframe.columns).index('includeHigh')
    includeLow_index = list(dataframe.columns).index('includeLow')
    includeTail_index = list(dataframe.columns).index('includeTail')

    for index in range(0, len(dataframe)):
        row = dataframe.ix[index]
        if index > 1:
            last_row = dataframe.ix[index - 1]
            if last_row["includeIndex"] != -1:
                # 前一根K线也是包含, 找此包含关系的第一根K线的前一根K线
                last_last_row = dataframe.ix[last_row["includeIndex"] - 1]
            else:
                last_last_row = dataframe.ix[index - 2]
            before_include_after = (last_row["includeHigh"] >= row["high"]) and (last_row["includeLow"] <= row["low"])
            after_include_before = (last_row["includeHigh"] <= row["high"]) and (last_row["includeLow"] >= row["low"])
            if before_include_after:
                # 前包后
                if last_last_row["includeHigh"] > last_row["includeHigh"]:
                    # 低低
                    dataframe.iloc[index, includeHigh_index] = row["high"]
                    dataframe.iloc[index, includeLow_index] = last_row["includeLow"]
                else:
                    # 高高
                    dataframe.iloc[index, includeHigh_index] = last_row["includeHigh"]
                    dataframe.iloc[index, includeLow_index] = row["low"]
                if last_row["includeIndex"] != -1:
                    dataframe.iloc[index, include_index] = last_row["includeIndex"]
                else:
                    dataframe.iloc[index, include_index] = index - 1
                    dataframe.iloc[index - 1, include_index] = index - 1

            elif after_include_before:
                # 后包前
                if last_last_row["includeHigh"] > last_row["includeHigh"]:
                    # 低低
                    dataframe.iloc[index, includeHigh_index] = last_row["includeHigh"]
                    dataframe.iloc[index, includeLow_index] = row["low"]
                else:
                    # 高高
                    dataframe.iloc[index, includeHigh_index] = row["high"]
                    dataframe.iloc[index, includeLow_index] = last_row["includeLow"]
                if last_row["includeIndex"] != -1:
                    dataframe.iloc[index, include_index] = last_row["includeIndex"]
                else:
                    dataframe.iloc[index, include_index] = index - 1
                    dataframe.iloc[index - 1, include_index] = index - 1
            else:
                dataframe.iloc[index, include_index] = -1
                dataframe.iloc[index, includeHigh_index] = row["high"]
                dataframe.iloc[index, includeLow_index] = row["low"]
                if dataframe.iloc[index - 1, include_index] != -1:
                    dataframe.iloc[index - 1, includeTail_index] = 1
            if (before_include_after or after_include_before) and index == len(dataframe) - 1:
                # 最后一根k线是包含
                dataframe.iloc[index, includeTail_index] = 1

        else:
            dataframe.iloc[index, include_index] = -1
            dataframe.iloc[index, includeHigh_index] = row["high"]
            dataframe.iloc[index, includeLow_index] = row["low"]


def handle_fenxing(dataframe):
    """
    处理分型
    :param dateframe:
    :return:
    """
    dataframe["fenxing"] = 0  # 0无分型 1顶分型 2底分型
    fenxing_index = list(dataframe.columns).index('fenxing')

    for index in range(0, len(dataframe)):
        row = dataframe.ix[index]
        if 0 < index < len(dataframe) - 1:
            # 包含
            if row["includeIndex"] != -1:
                # 并且是包含关系的最后一根K线
                if row["includeTail"]:
                    # 取包含关系的第一根K线的前一根K线作为last
                    last_row = dataframe.ix[row["includeIndex"] - 1]
                else:
                    continue
            else:
                last_row = dataframe.ix[index - 1]
            next_row = dataframe.ix[index + 1]

            if last_row["includeHigh"] > row["includeHigh"] and next_row["includeHigh"] > row["includeHigh"]:
                # 底分型
                dataframe.iloc[index, fenxing_index] = 2
            elif last_row["includeHigh"] < row["includeHigh"] and next_row["includeHigh"] < row["includeHigh"]:
                # 顶分型
                dataframe.iloc[index, fenxing_index] = 1


def handle_pen(dataframe, start=0):
    """
    处理笔，首先画严格笔
    :param dataframe:
    :return:
    """

    # 1. 找出第一个能成笔的顶底分型
    first_index = -1
    first_matched_index = -1
    for index in range(start, len(dataframe)):
        row = dataframe.ix[index]
        if row["fenxing"]:
            first_matched_index = search_match_fenxing(dataframe, index)
            if first_matched_index > 0:
                first_index = index
                break
    if first_index == -1:
        return

    pens = [{
        "start": first_index,
        "end": first_matched_index
    }]

    # 2. 找笔
    index = first_matched_index
    while True:
        print "搜索index:%s" % index
        matched_index = search_match_fenxing(dataframe, index)
        if matched_index == -1:
            print "搜索index:%s 遍历结束无法找到匹配分型" % index
            break
        elif matched_index == -2:
            ret = fix_pen(pens)
            if ret == -1:
                break
            else:
                index = ret
        else:
            print "搜索index:%s 找到匹配分型%s" % (index, matched_index)
            pens.append({"start": index, "end": matched_index})
            index = matched_index
    if not pens and start < len(dataframe):
        print("找到的初始分型导致无法找到任何笔，继续找一个正确的初始分型")
        return handle_pen(dataframe, start=first_matched_index + 1)
    return pens


def fix_pen(pens):
    """
    修正笔
    :return: -1：修正笔结束，没有形成笔  其他：找到修正笔
    """
    # 该分型无法成笔，需要修正上一个笔
    if not pens:
        return -1
    last_pen = pens[-1]
    del pens[-1]
    print "搜索index:%s 该分型无法成笔，需要修正上一个笔" % last_pen["end"]
    matched_index = search_match_fenxing(dataframe, last_pen["start"], last_pen["end"])
    print "修正笔index:%s" % last_pen["start"]
    if matched_index == -1:
        print "修正笔index:%s 遍历结束无法找到匹配分型" % last_pen["start"]
        return -1
    elif matched_index == -2:
        print "修正笔index:%s 该分型无法成笔,需要再往前修正" % last_pen["start"]
        return fix_pen(pens)
    last_pen["end"] = matched_index
    pens.append(last_pen)
    print "修正笔index:%s 找到匹配分型%s" % (last_pen["start"], matched_index)
    return matched_index


def search_match_fenxing(dataframe, index, search_after=-1):
    """

    :param dataframe:
    :param index:
    :param search_after:
    :return:  -1 遍历完没发现匹配分型  -2 因为有更高的顶分型或更低的底分型无法匹配
    """

    prev = dataframe.ix[index]
    kline_count = 1  # 记录K线数量
    secondary_has_pen = False
    secondary_pen_enable = False  # 是否可能次高低点成笔
    if search_after != -1:
        if prev["fenxing"] == 1:
            highest = prev["includeHigh"]  # 记录遍利过的最高点
            lowest = dataframe.ix[search_after]["includeLow"]  # 记录遍历过的最低点
        else:
            highest = dataframe.ix[search_after]["includeHigh"]  # 记录遍利过的最高点
            lowest = prev["includeLow"]  # 记录遍历过的最低点
        secondary_has_pen = True
    else:
        highest = prev["includeHigh"]  # 记录遍利过的最高点
        lowest = prev["includeLow"]  # 记录遍历过的最低点
    for i in range(index + 1, len(dataframe)):
        cur = dataframe.ix[i]
        if cur["includeIndex"] != -1 and not cur["includeTail"]:
            continue
        if prev["fenxing"] == 1 and cur["includeHigh"] > prev["includeHigh"]:
            return -2
        elif prev["fenxing"] == 2 and cur["includeLow"] < prev["includeLow"]:
            return -2

        kline_count += 1
        if i <= search_after:
            continue
        if PEN_TYPE == STRICT_PEN and cur["fenxing"] == prev["fenxing"] and secondary_pen_enable:
            if cur["fenxing"] == 1:
                secondary_back_deep = (cur["includeHigh"] - lowest) / (highest - lowest)
            else:
                secondary_back_deep = (highest - cur["includeLow"]) / (highest - lowest)
            # 回荡深度是否超过50%
            if secondary_back_deep > 0.5:
                secondary_pen_enable = False

        if cur["fenxing"] + prev["fenxing"] == 3:
            # 分型匹配
            if PEN_TYPE == STRICT_PEN:
                # 严格笔
                if kline_count >= 5 and secondary_has_pen:
                    if cur["fenxing"] == 1:
                        if cur["includeHigh"] > highest:
                            return i
                        elif secondary_pen_enable:
                            print "次高点成笔"
                            return i
                    if cur["fenxing"] == 2:
                        if cur["includeLow"] < lowest:
                            return i
                        elif secondary_pen_enable:
                            print "次低点成笔"
                            return i
                elif kline_count == 4:
                    # 次高低点成笔
                    secondary_pen_enable = True
            elif PEN_TYPE == DERIVATION_PEN and secondary_has_pen:
                # 推笔
                if cur["fenxing"] == 1:
                    # if cur["includeHigh"] > highest:
                    return i
                if cur["fenxing"] == 2:
                    # if cur["includeLow"] < lowest:
                    return i

            if cur["fenxing"] == 1 and highest < cur["includeHigh"]:
                highest = cur["includeHigh"]
            elif cur["fenxing"] == 2 and lowest > cur["includeLow"]:
                lowest = cur["includeLow"]
            secondary_has_pen = True
    return -1


def handle_segment(pens):
    """
    处理线段
    线段的终结
    :return:
    """

    divides = []
    if not pens and len(pens) < 3: return divides
    signature_sequence_index = 0  # 当前特征序列在pens列表中的索引
    current_pen = Pen.create_by_dict(context, signature_sequence_index, pens[signature_sequence_index])

    # 始终把初始走势当成上涨线段
    # 第一笔下跌，这一笔是特征序列的0号
    # 第一笔上涨，就把第二笔当作特征序列的0号，不管第一笔
    if current_pen.is_rise:
        # 第一笔上涨，就把第二笔当作特征序列的0号，不管第一笔
        signature_sequence_index += 1
        current_pen = Pen.create_by_dict(context, signature_sequence_index, pens[signature_sequence_index])

    current_signature = SignatureSequenceItem.create_by_pen(current_pen)
    signature_sequence_index += 2
    while signature_sequence_index < len(pens):
        next_signature = SignatureSequenceItem.create_by_pen(Pen.create_by_dict(context, signature_sequence_index, pens[
            signature_sequence_index]))  # 特征序列的1号
        relation, ret_signature = current_signature.grow(next_signature)
        if relation == SignatureSequenceItem.EXTEND:
            # 线段的延伸
            current_signature = ret_signature
            signature_sequence_index += 2
        else:
            # 线段的转折
            pen = Pen.create_by_dict(context, ret_signature.extremum_pen_index, pens[ret_signature.extremum_pen_index])
            if pen.is_rise:
                divides.append(pen.end)
            else:
                divides.append(pen.start)
            signature_sequence_index += 1
            if signature_sequence_index >= len(pens):
                break
            current_signature = SignatureSequenceItem.create_by_pen(
                Pen.create_by_dict(context, signature_sequence_index, pens[
                    signature_sequence_index]))  # 特征序列的1号
            signature_sequence_index += 2
    print divides
    return divides


class SignatureSequenceItem(object):
    """
    特征序列


    """

    EXTEND = 1  # 延伸
    TURN = 2  # 转折

    def __init__(self, context, is_rise, extremum_pen_index, high, low):
        self.context = context
        self.is_rise = is_rise
        self.extremum_pen_index = extremum_pen_index  # 极值点笔索引。极值点：上升线段的最高点，下降线段的最低点
        # 高低点用作包含关系和分型的判断
        self.high = high  # 高点
        self.low = low  # 低点

    def __str__(self):
        return "is_rise:%s,extremum_pen_index:%s,high:%s,low:%s" % (
            self.is_rise, self.extremum_pen_index, self.high, self.low)

    @classmethod
    def create_by_pen(cls, pen):
        """
        :type pen:Pen
        :return:
        """
        return SignatureSequenceItem(pen.context, not pen.is_rise, pen.index, pen.high, pen.low)

    def grow(self, next_signature):
        """
            特征序列的生长
            特征序列之间的二种关系：
            延伸：沿着线段方向运行，可能有相互包含
            转折：特征序列形成了分型，导致线段终结
        :type next_signature: SignatureSequenceItem
        :param next_signature:
        :return: relation, signature : 特征序列关系 和 极值特征序列
        """
        if self.high < next_signature.high and self.low < next_signature.low and self.is_rise or \
                self.high > next_signature.high and self.low > next_signature.low and not self.is_rise:
            # 延伸，没有包含
            relation = SignatureSequenceItem.EXTEND
            if self.is_rise:
                return relation, next_signature
            else:
                return relation, self
        elif self.high < next_signature.high and self.low < next_signature.low and not self.is_rise or \
                self.high > next_signature.high and self.low > next_signature.low and self.is_rise:
            # 直接转折
            relation = SignatureSequenceItem.TURN
            if self.is_rise:
                return relation, self
            else:
                return relation, next_signature
        else:
            # 处于包含关系, 但也算延伸
            relation = SignatureSequenceItem.EXTEND
            if self.low < next_signature.low and self.high > next_signature.high:
                # 左包含右
                if self.is_rise:
                    ret_signature = SignatureSequenceItem(self.context, self.is_rise, self.extremum_pen_index,
                                                          self.high,
                                                          next_signature.low)
                else:
                    ret_signature = SignatureSequenceItem(self.context, self.is_rise, self.extremum_pen_index,
                                                          next_signature.high,
                                                          self.low)
            else:
                # 右包含左
                if self.is_rise:
                    ret_signature = SignatureSequenceItem(self.context, self.is_rise, next_signature.extremum_pen_index,
                                                          next_signature.high,
                                                          self.low)
                else:
                    ret_signature = SignatureSequenceItem(self.context, self.is_rise, next_signature.extremum_pen_index,
                                                          self.high,
                                                          next_signature.low)
            return relation, ret_signature


class Pen(object):
    """
    笔
    """

    def __init__(self, context, index, start, end):
        self.index = index
        self.context = context
        self.dataframe = self.context.dataframe
        self.start = start
        self.end = end
        start_high = self.context.get_k_include_high(self.start)
        end_high = self.context.get_k_include_high(self.end)

        start_low = self.context.get_k_include_low(self.start)
        end_low = self.context.get_k_include_low(self.end)
        self.is_rise = start_high < end_high  # 是否上涨一笔
        self.high = end_high if self.is_rise else start_high
        self.low = start_low if self.is_rise else end_low

    def to_dict(self):
        return {
            "start": self.start,
            "end": self.end
        }

    def __str__(self):
        return "index:%s,start:%s,end:%s" % (self.index, self.start, self.end)

    @classmethod
    def create_by_dict(cls, context, index, pen_dict):
        return Pen(context, index, pen_dict["start"], pen_dict["end"])


class Context(object):

    def __init__(self, dataframe):
        self.dataframe = dataframe

    def get_k_include_high(self, index):
        return self.dataframe.ix[index]["includeHigh"]

    def get_k_include_low(self, index):
        return self.dataframe.ix[index]["includeLow"]


CIWEN = "SZ002343"
SHUGUANG = "SH603019"
CHUANGYEBAN = "SZ399006"
SHANGZHENG = "SH000001"
context = None

if __name__ == '__main__':
    while True:
        end_date = int(time.time())
        # dataframe = getKLineData("600887.SS", scale=MINUTE_5, start_date="20181010", end_date="20181118")
        dataframe = getKLineData(SHANGZHENG, scale=MINUTE_5, count=3000)
        app_log.info("开始处理数据：%s", datetime.datetime.now())
        global context
        context = Context(dataframe)
        handle_include(dataframe)
        handle_fenxing(dataframe)
        pens = handle_pen(dataframe)
        divides = handle_segment(pens)

        # dataframe_60 = getKLineData("600887.SS", scale=MINUTE_60, start_date="20181010", end_date="20181118")
        # dataframe_60 = getKLineData("SH603019", scale=MINUTE_60, count=len(dataframe) / 12)
        # handle_include(dataframe_60)
        # handle_fenxing(dataframe_60)
        # pens_60 = handle_pen(dataframe_60)
        # if pens_60:
        #     print dataframe_60.ix[pens_60[0]["start"]]

        app_log.info("处理数据完毕：%s", datetime.datetime.now())

        json_str = dataframe.to_json(orient="records")
        data = json.loads(json_str)
        data = {"kline": data, "pens": pens}
        with open("../static/data.json", "w") as fp:
            json.dump(data, fp)
            fp.close()
        # break
        time.sleep(60)

    # plt.figure()
    # pl = dataframe.plot.box()
    # plt.show()
