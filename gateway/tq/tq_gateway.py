# coding=utf-8
import datetime
from threading import Thread
from typing import List

from pandas import DataFrame

from event.engine import EventEngine
from trader.constant import Interval, Exchange, Direction, Offset
from trader.gateway import BaseGateway
from trader.object import KLineRequest, BarData, SubscribeBarRequest, OrderRequest

OFFSET_DICT = {
    Offset.OPEN: "OPEN",
    Offset.CLOSE: "CLOSE",
    Offset.CLOSETODAY: "CLOSETODAY",
}

DIRECTION_DICT = {
    Direction.LONG: "BUY",
    Direction.SHORT: "SELL"
}

__author__ = "hanweiwei"
__date__ = "2019-05-31"

from tqsdk import api, TqSim, TqBacktest


def _bar_interval_2_seconds(bar_interval):
    """

    :param bar_interval:
    :return:
    """
    if bar_interval == Interval.MINUTE:
        seconds = 60
    elif bar_interval == Interval.MINUTE_5:
        seconds = 300
    elif bar_interval == Interval.MINUTE_30:
        seconds = 1800
    elif bar_interval == Interval.HOUR:
        seconds = 3600
    elif bar_interval == Interval.DAILY:
        seconds = 3600 * 24
    elif bar_interval == Interval.WEEKLY:
        seconds = 3600 * 24 * 7
    else:
        raise ValueError("unknown bar interval %s" % bar_interval)
    return seconds


def _direction(direction: Direction):
    return DIRECTION_DICT.get(direction)


def _offset(offset: Offset):
    return OFFSET_DICT.get(offset)


class TQGateway(BaseGateway):

    def __init__(self, event_engine: EventEngine):
        super().__init__(event_engine, "TQ")
        self._tqapi = api.TqApi(TqSim(), backtest=TqBacktest(start_dt=datetime.date(2019, 3, 20),
                                                             end_dt=datetime.date(2019, 6, 20)))
        self._looper = Thread(target=self._run)

        self._bar_requests: List[SubscribeBarRequest] = []
        self._bars_df: List[DataFrame] = []

    def get_kline_data(self, kline_request: KLineRequest):
        exchange = kline_request.exchange
        interval = kline_request.bar_interval
        seconds = _bar_interval_2_seconds(kline_request.bar_interval)
        symbol = f'{kline_request.exchange.value}.{kline_request.symbol}'
        df = self._tqapi.get_kline_serial(symbol, duration_seconds=seconds,
                                          data_length=kline_request.data_length)
        data: List[BarData] = []
        for ix, row in df.iterrows():
            bar = self.dfrow2bar(exchange, kline_request.symbol, interval, row)
            data.append(bar)

        return data

    def dfrow2bar(self, exchange, symbol, interval, row):
        return BarData(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            datetime=datetime.datetime.fromtimestamp(int(row["datetime"] / 1000000000)),
            open_price=row["open"],
            high_price=row["high"],
            low_price=row["low"],
            close_price=row["close"],
            volume=row["volume"],
            gateway_name=self.gateway_name
        )

    def connect(self, setting: dict):
        # self._looper.start()
        self._run()

    def subscribe_bar(self, req: SubscribeBarRequest):
        seconds = _bar_interval_2_seconds(req.interval)
        symbol = f'{req.exchange.value}.{req.symbol}'
        df = self._tqapi.get_kline_serial(symbol, duration_seconds=seconds)
        self._bars_df.append(df)
        self._bar_requests.append(req)

    def send_order(self, req: OrderRequest):
        symbol = f'{req.exchange.value}.{req.symbol}'
        direction = _direction(req.direction)
        offset = _offset(req.offset)
        order = self._tqapi.insert_order(symbol=symbol, direction=direction, offset=offset, volume=int(req.volume))

    def query_position(self):
        pass

    def _run(self):
        while True:
            self._tqapi.wait_update()
            for i, bar_df in enumerate(self._bars_df):
                if self._tqapi.is_changing(bar_df.iloc[-1], "datetime"):
                    row = bar_df.iloc[-2]
                    bar_request = self._bar_requests[i]
                    bar = self.dfrow2bar(bar_request.exchange, bar_request.symbol, bar_request.interval, row)
                    self.on_bar(bar)
