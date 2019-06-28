# coding=utf-8
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session

from chan.db.object import Base, BaseDO

__author__ = "hanweiwei"
__date__ = "2019-06-06"

# 初始化数据库连接:
engine = create_engine('sqlite:////Users/hanweiwei/PycharmProjects/QuantChan/chan.db', echo=False)
BaseDO.metadata.create_all(engine)
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)


# 创建DBSession类型:


def get_session():
    """
    :rtype : Session
    :return:
    """
    return DBSession()
