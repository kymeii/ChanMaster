# coding=utf-8

from sqlalchemy import Column, String, INT, FLOAT, DATETIME, BOOLEAN
from sqlalchemy.ext.declarative import declarative_base

__author__ = "hanweiwei"
__date__ = "2019-06-03"


class Base(object):
    pass
    # def to_json(self):
    #     dict = self.__dict__
    #     if "_sa_instance_state" in dict:
    #         del dict["_sa_instance_state"]
    #     return dict


# 创建对象的基类:
BaseDO = declarative_base(Base)


# 定义User对象:
class ChanBarDataDO(BaseDO):
    """
    create table chan_bar_data
    (
      gateway       VARCHAR(10) not null,
      exchange      VARCHAR(10) not null,
      symbol         VARCHAR(10) not null,
      datetime      DATETIME    not null,
      interval      VARCHAR(5)  not null,
      volume        INT,
      open_price    FLOAT,
      close_price   FLOAT,
      high_price    FLOAT,
      low_price     FLOAT,
      include_high  FLOAT,
      include_low   FLOAT,
      include_index INT,
      include_tail  INT,
      primary key (gateway, exchange, symbol, datetime, interval)
    )
    IF NOT EXISTS;
    """

    # 表的名字:
    __tablename__ = 'chan_bar_data'

    # 表的结构:
    gateway = Column(String(10), primary_key=True)
    exchange = Column(String(10), primary_key=True)
    symbol = Column(String(10), primary_key=True)
    interval = Column(String(5), primary_key=True)
    datetime = Column(DATETIME, primary_key=True)
    volume = Column(INT)
    open_price = Column(FLOAT)
    close_price = Column(FLOAT)
    high_price = Column(FLOAT)
    low_price = Column(FLOAT)
    include_high = Column(FLOAT)
    include_low = Column(FLOAT)
    include_index = Column(INT)
    include_tail = Column(INT)


class PenDO(BaseDO):
    __tablename__ = 'pen'

    # 表的结构:
    gateway = Column(String(10), primary_key=True)
    exchange = Column(String(10), primary_key=True)
    symbol = Column(String(10), primary_key=True)
    interval = Column(String(5), primary_key=True)
    start_datetime = Column(DATETIME, primary_key=True)
    end_datetime = Column(DATETIME, primary_key=True)
    is_rise = Column(BOOLEAN)


class CentreDO(BaseDO):
    __tablename__ = 'centre'

    # 表的结构:
    gateway = Column(String(10), primary_key=True)
    exchange = Column(String(10), primary_key=True)
    symbol = Column(String(10), primary_key=True)
    interval = Column(String(5), primary_key=True)
    start_datetime = Column(DATETIME, primary_key=True)
    end_datetime = Column(DATETIME, primary_key=True)
    high = Column(FLOAT)
    low = Column(FLOAT)
    is_rise = Column(BOOLEAN)
