# coding=utf-8
from chan.db.object import ChanBarDataDO, PenDO, CentreDO
from chan.object import ChanBarData, Pen, Centre

__author__ = "hanweiwei"
__date__ = "2019-06-03"


class ChanBarDataMP:

    def mapper(self, chan_bar_data: ChanBarData):
        """

        :param chan_bar_data:
        :rtype :ChanBarDataDO
        :return:
        """
        return ChanBarDataDO(
            gateway=chan_bar_data.gateway_name,
            exchange=chan_bar_data.exchange.value,
            symbol=chan_bar_data.symbol,
            datetime=chan_bar_data.datetime,
            interval=chan_bar_data.interval.value,
            volume=chan_bar_data.volume,
            open_price=chan_bar_data.open_price,
            close_price=chan_bar_data.close_price,
            high_price=chan_bar_data.high_price,
            low_price=chan_bar_data.low_price,
            include_high=chan_bar_data.include_high,
            include_low=chan_bar_data.include_low,
            include_index=chan_bar_data.include_index,
            include_tail=chan_bar_data.include_tail
        )


class PenMP:

    def mapper(self, pen: Pen):
        """

        :param pen:
        :rtype :PenDO
        :return:
        """
        return PenDO(
            gateway=pen.start_bar().gateway_name,
            exchange=pen.start_bar().exchange.value,
            symbol=pen.start_bar().symbol,
            interval=pen.start_bar().interval.value,
            start_datetime=pen.start_bar().datetime,
            end_datetime=pen.end_bar().datetime,
            is_rise=pen.is_rise
        )


class CentreMP:

    def mapper(self, centre: Centre):
        """

        :param centre:
        :rtype :CentreDO
        :return:
        """
        return CentreDO(
            gateway=centre.start_pen.start_bar().gateway_name,
            exchange=centre.start_pen.start_bar().exchange.value,
            symbol=centre.start_pen.start_bar().symbol,
            interval=centre.start_pen.start_bar().interval.value,
            start_datetime=centre.start_pen.start_bar().datetime,
            end_datetime=centre.end_pen.end_bar().datetime,
            is_rise=centre.is_rise,
            high=centre.high,
            low=centre.low
        )
