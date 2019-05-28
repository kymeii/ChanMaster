# coding=utf-8
import urllib2
import pandas as pd
import re

from app import app_log

__author__ = "hanweiwei"
__date__ = "2018/10/25"

KLINE_URL = "https://money.finance.sina.com.cn/quotes_service/api/jsonp_v2.php/data=/CN_MarketData.getKLineData?symbol=%s&scale=%s&ma=%s&datalen=%s"

MINUTE_5 = 5
MINUTE_15 = 15
MINUTE_30 = 30
MINUTE_60 = 60
DAY = 240
DAY_5 = DAY * 5
WEEK = DAY * 7
MONTH = DAY * 30


def getKLineData(stock_code="SZ000001", scale=DAY, ma="no", count=100):
    """
    查询K线
    :param stock_code: 股票代码 SZ深圳000001 SH上证600001
    :param scale: 周期 5m 15m 30m 60m 1day 5day 1week 1month
    :param ma: 移动平均线 ,分隔
    :param count: 数量
    :return: DataFrame
    """
    contents = urllib2.urlopen(KLINE_URL % (stock_code, scale, ma, count)).read()
    contents = contents[6:-1]

    contents = re.sub(r",(\w+):", lambda s: ',"%s":' % contents[s.start(1):s.end(1)], contents)
    contents = re.sub(r"{(\w+):", lambda s: '{"%s":' % contents[s.start(1):s.end(1)], contents)
    app_log.info("获取数据成功")
    return pd.read_json(contents)


if __name__ == '__main__':
    print getKLineData("SH000001", scale=MINUTE_60, count=100)
