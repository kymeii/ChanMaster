# coding=utf-8
from typing import List

from chan.db.db_helper import get_session
from chan.db.object import PenDO, ChanBarDataDO, CentreDO
from chan.mapper import ChanBarDataMP, PenMP, CentreMP
from chan.object import ChanBarData, Pen, Centre

__author__ = "hanweiwei"
__date__ = "2019-06-06"


class ChanBarDataDao():

    def __init__(self):
        self.chan_bar_data_mp = ChanBarDataMP()

    def insert(self, chan_bar_data: ChanBarData):
        chan_bar_data_do = self.chan_bar_data_mp.mapper(chan_bar_data)

        # 创建session对象:
        session = get_session()
        # 添加到session:
        session.merge(chan_bar_data_do)
        # 提交即保存到数据库:
        session.commit()
        # 关闭session:
        session.close()

    def select(self, gateway, exchange, symbol, interval, limit):
        session = get_session()
        bars: List = session.query(ChanBarDataDO) \
            .filter(ChanBarDataDO.gateway == gateway) \
            .filter(ChanBarDataDO.exchange == exchange) \
            .filter(ChanBarDataDO.symbol == symbol) \
            .filter(ChanBarDataDO.interval == interval) \
            .order_by(ChanBarDataDO.datetime.desc()) \
            .limit(limit) \
            .all()
        session.close()
        bars.reverse()
        return bars


class PenDao():

    def __init__(self):
        self.pen_mp = PenMP()

    def insert(self, pen: Pen):
        pen_do = self.pen_mp.mapper(pen)

        # 创建session对象:
        session = get_session()
        # 添加到session:

        old_pen = session.query(PenDO) \
            .filter(PenDO.gateway == pen_do.gateway) \
            .filter(PenDO.exchange == pen_do.exchange) \
            .filter(PenDO.symbol == pen_do.symbol) \
            .filter(PenDO.interval == pen_do.interval) \
            .filter(PenDO.start_datetime == pen_do.start_datetime) \
            .first()
        if old_pen:
            session.delete(old_pen)
        session.add(pen_do)
        # 提交即保存到数据库:
        session.commit()
        # 关闭session:
        session.close()

    def select(self, gateway, exchange, symbol, interval, start_time):
        session = get_session()
        pens: List[PenDO] = session.query(PenDO) \
            .filter(PenDO.gateway == gateway) \
            .filter(PenDO.exchange == exchange) \
            .filter(PenDO.symbol == symbol) \
            .filter(PenDO.interval == interval) \
            .filter(PenDO.start_datetime >= start_time) \
            .all()
        session.close()
        return pens

    def delete(self, pen: Pen):
        pen_do = self.pen_mp.mapper(pen)

        # 创建session对象:
        session = get_session()
        # 添加到session:

        old_pen = session.query(PenDO) \
            .filter(PenDO.gateway == pen_do.gateway) \
            .filter(PenDO.exchange == pen_do.exchange) \
            .filter(PenDO.symbol == pen_do.symbol) \
            .filter(PenDO.interval == pen_do.interval) \
            .filter(PenDO.start_datetime == pen_do.start_datetime) \
            .first()
        if old_pen:
            session.delete(old_pen)
        # 提交即保存到数据库:
        session.commit()
        # 关闭session:
        session.close()


class CentreDao():

    def __init__(self):
        self.centre_mp = CentreMP()

    def insert(self, centre: Centre):
        centre_do = self.centre_mp.mapper(centre)

        # 创建session对象:
        session = get_session()
        # 添加到session:

        old_centre = session.query(CentreDO) \
            .filter(CentreDO.gateway == centre_do.gateway) \
            .filter(CentreDO.exchange == centre_do.exchange) \
            .filter(CentreDO.symbol == centre_do.symbol) \
            .filter(CentreDO.interval == centre_do.interval) \
            .filter(CentreDO.start_datetime == centre_do.start_datetime) \
            .first()
        if old_centre:
            session.delete(old_centre)
        session.add(centre_do)
        # 提交即保存到数据库:
        session.commit()
        # 关闭session:
        session.close()

    def select(self, gateway, exchange, symbol, interval, start_time):
        session = get_session()
        centres: List[CentreDO] = session.query(CentreDO) \
            .filter(CentreDO.gateway == gateway) \
            .filter(CentreDO.exchange == exchange) \
            .filter(CentreDO.symbol == symbol) \
            .filter(CentreDO.interval == interval) \
            .filter(CentreDO.start_datetime >= start_time) \
            .all()
        session.close()
        return centres
