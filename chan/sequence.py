# coding=utf-8

__author__ = "hanweiwei"
__date__ = "2019-06-09"


class SignatureSequenceItem(object):
    """
    特征序列


    """
    EXTEND = 1  # 延伸
    TURN = 2  # 转折
    INCLUDE = 3  # 包含

    def __init__(self, is_rise, extremum_pen_index, high, low):
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
        return SignatureSequenceItem(not pen.is_rise, pen.index, pen.high(), pen.low())

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
            return relation, next_signature

        elif self.high < next_signature.high and self.low < next_signature.low and not self.is_rise or \
                self.high > next_signature.high and self.low > next_signature.low and self.is_rise:
            # 直接转折
            relation = SignatureSequenceItem.TURN
            # if self.is_rise:
            return relation, self
            # else:
            #     return relation, next_signature
        else:
            # 处于包含关系, 但也算延伸
            relation = SignatureSequenceItem.EXTEND
            if self.low <= next_signature.low and self.high >= next_signature.high:
                # 左包含右
                if self.is_rise:
                    ret_signature = SignatureSequenceItem(self.is_rise, self.extremum_pen_index,
                                                          self.high,
                                                          next_signature.low)
                else:
                    ret_signature = SignatureSequenceItem(self.is_rise, self.extremum_pen_index,
                                                          next_signature.high,
                                                          self.low)
            else:
                # if self.is_rise:
                ret_signature = next_signature
                # 笔破坏
                if self.is_rise:
                    ret_signature = SignatureSequenceItem(self.is_rise, next_signature.extremum_pen_index,
                                                          next_signature.high,
                                                          self.low)
                else:
                    ret_signature = SignatureSequenceItem(self.is_rise, next_signature.extremum_pen_index,
                                                          self.high,
                                                          next_signature.low)
            return relation, ret_signature
