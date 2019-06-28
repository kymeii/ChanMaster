# coding=utf-8
import datetime

import pandas as pd
import pytz
import requests
import requests_cache

from app import app_log
from tools import time_tools

__author__ = "hanweiwei"
__date__ = "2018/11/12"

KLINE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/SYMBOL?" \
            "symbol=SYMBOL" \
            "&period1=PERIOD1" \
            "&period2=PERIOD2" \
            "&interval=INTERVAL" \
            "&includePrePost=true" \
            "&events=div%7Csplit%7Cearn" \
            "&lang=zh-Hant-HK" \
            "&region=HK" \
            "&crumb=x3Yc9Jik83n" \
            "&corsDomain=hk.finance.yahoo.com"

MINUTE_1 = "1m"
MINUTE_2 = "2m"
MINUTE_5 = "5m"
MINUTE_15 = "15m"
MINUTE_60 = "60m"
DAY = "1d"

requests_cache.install_cache()
s = requests.Session()


def getKLineData(stock_code, scale, start_date, end_date):
    """
    查询K线
    :param stock_code: 股票代码 深圳 000001.SZ  上海 600001.SS
    :param scale: 周期 1m 5m 15m 30m 60m 1d 1w 1mo
    :param start_date: timestamp or date or str or datetime
    :param end_date: timestamp or date or str or datetime
    :return: DataFrame
    """

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    now = datetime.datetime.now()
    if not start_date:
        start_date = time_tools.datetime2timestamp(now + datetime.timedelta(days=-100))
    if not end_date:
        end_date = time_tools.datetime2timestamp(now)

    url = KLINE_URL \
        .replace("SYMBOL", stock_code) \
        .replace("PERIOD1", str(start_date)) \
        .replace("PERIOD2", str(end_date)) \
        .replace("INTERVAL", scale)
    app_log.info("REQUEST START:\n%s" % url)

    response = s.get(url, headers={'Connection': 'keep-alive',
                                   "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"})
    contents = response.json()
    print(response.headers)
    app_log.info("REQUEST END:\n%s" % response)

    chart = contents["chart"]
    if chart["error"]:
        raise Exception(contents["error"])
    contents = chart["result"][0]
    quote = contents["indicators"]["quote"][0]
    datetime_index = pd.to_datetime(contents["timestamp"], unit="s", utc=True)
    datetime_index = datetime_index.tz_convert(pytz.timezone("Asia/Shanghai"))
    data = pd.DataFrame({
        "high": quote["high"]
        , "low": quote["low"]
        , "open": quote["open"]
        , "close": quote["close"]
    }, index=datetime_index)

    data = data.dropna(how='any')
    data['timestamp'] = data.index
    data['day'] = ""
    day_index = list(data.columns).index('day')

    for i in range(0, len(data)):
        day = data['timestamp'][i]
        data.iloc[i, day_index] = day.strftime("%Y-%m-%d %H:%M:%SZ")
    return data


def parse_date(date):
    """

    :param date: timestamp or date or str or datetime
    :return:
    """
    if date:
        if isinstance(date, str):
            date = time_tools.datetime2timestamp(datetime.datetime.strptime(date, "%Y%m%d"))
        elif isinstance(date, datetime.date):
            date = time_tools.date2timestamp(date)
        elif isinstance(date, datetime.datetime):
            date = time_tools.date2timestamp(date)
        elif isinstance(date, int):
            pass
        else:
            raise ValueError("date type error, must be timestamp, date, datetime, str")
    return date


if __name__ == '__main__':
    app_log.info("\n%s", getKLineData("601788.SS", scale=MINUTE_5, start_date="20181111", end_date="20181114"))
    # print getKLineData("601788.SS", scale=MINUTE_5, start_date="20181109", end_date="20181111")
