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

KLINE_URL = "http://api.tushare.pro"

requests_cache.install_cache()
s = requests.Session()


def getKLineData(stock_code, scale, start_date, end_date):
    """
    查询K线
    :param stock_code: 股票代码 深圳 000001.SZ  上海 600001.SS
    :param scale: 周期 1min 5min 30min 60min 1d
    :param start_date: str
    :param end_date: str
    :return: DataFrame
    """

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    api_params = {
        "ts_code": stock_code,
        "start_date": start_date,
        "end_date": end_date,
        "adj": "qfq",
        "freq": scale
    }
    params = {"api_name": "hist_bar", "token": TOKEN, "params": api_params, "fields": "open,high,low,close"}

    app_log.info("REQUEST START:\n%s\%s", KLINE_URL, api_params)

    response = s.post(KLINE_URL, headers={'Connection': 'keep-alive',
                                          "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"}
                      , json=params)
    contents = response.json()
    # app_log.info("REQUEST END:\n%s" % response)
    #
    # chart = contents["chart"]
    # if chart["error"]:
    #     raise Exception(contents["error"])
    # contents = chart["result"][0]
    # quote = contents["indicators"]["quote"][0]
    # datetime_index = pd.to_datetime(contents["timestamp"], unit="s", utc=True)
    # datetime_index = datetime_index.tz_convert(pytz.timezone("Asia/Shanghai"))
    # data = pd.DataFrame({
    #     "high": quote["high"]
    #     , "low": quote["low"]
    #     , "open": quote["open"]
    #     , "close": quote["close"]
    # }, index=datetime_index)
    #
    # data = data.dropna(how='any')
    # data['time'] = data.index
    return contents


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
    data = getKLineData("601788.SS", scale=MINUTE_5, start_date="20181111", end_date="20181114")
    app_log.info("\n%s", json.dumps(data,ensure_ascii=False))
    # print getKLineData("601788.SS", scale=MINUTE_5, start_date="20181109", end_date="20181111")
