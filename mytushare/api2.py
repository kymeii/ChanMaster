# coding=utf-8
import datetime
import json

import requests
import requests_cache

from app import app_log
from tools import time_tools

__author__ = "hanweiwei"
__date__ = "2018/11/16"
TOKEN = "24b9e438d14d30648fa32dd6b457500ddc041ff0e17378d0b2083d7d"

MINUTE_1 = "1MIN"
MINUTE_5 = "5MIN"
MINUTE_30 = "30MIN"
MINUTE_60 = "60MIN"
DAY_1 = "1D"

import tushare as  tu

tu.set_token(TOKEN)
pro_api = tu.pro_api()


def getKLineData(stock_code, scale, start_date, end_date):
    """
    查询K线
    :param stock_code: 股票代码 深圳 000001.SZ  上海 600001.SS
    :param scale: 周期 1min 5min 30min 60min 1d
    :param start_date: str
    :param end_date: str
    :return: DataFrame
    """
    return tu.pro_bar(stock_code, pro_api, start_date, end_date, freq=scale, adj="qfq")


if __name__ == '__main__':
    data = getKLineData("000001.SZ", scale=None, start_date="20181101", end_date="20181118")
    app_log.info("\n%s", data)
    # print getKLineData("601788.SS", scale=MINUTE_5, start_date="20181109", end_date="20181111")
