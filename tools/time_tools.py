# coding=utf-8
import time

import datetime

__author__ = "hanweiwei"
__date__ = "2018/9/20"


def timestamp():
    return int(time.time())


def is_today(t):
    today = datetime.datetime.today()
    return t.day == today.day and t.month == today.month and t.year == today.year


def timedelta(old, new):
    return new - old


def datetime2timestamp(datetime_param):
    """

    :param datetime_param:
    :type datetime_param: datetime.datetime
    :return:
    """
    return int(time.mktime(datetime_param.timetuple()))


def date2timestamp(date_param):
    """

    :param datetime_param:
    :type datetime_param: datetime.date
    :return:
    """
    return int(time.mktime(date_param.timetuple()))


def m1_2_m5(m1: datetime.datetime):
    return m1.replace(minute=m1.minute - m1.minute % 5)

def m5_2_m30(m1: datetime.datetime):
    return m1.replace(minute=m1.minute - m1.minute % 30)
