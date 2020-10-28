# coding=utf-8

from __future__ import absolute_import

__author__ = "hanweiwei"
__date__ = "2020/10/18"

"""
北上资金布林轨，择时使用
"""

from jqdatasdk import *
import matplotlib.pyplot as pl
import datetime

import matplotlib.dates as mdates

STDEV_N = 2  # 计算布林轨的标准差倍数
WINDOW = 60  # 计算布林轨的窗口长度


def get_boll(end_date):
    """
    获取北向资金布林带
    """

    _base_days = get_trade_days(end_date=end_date, count=100)  # 基础

    _mfs = []
    _MiD = []  # 日平均线数组
    _UP = []
    _DW = []
    _DT = []
    for i in _base_days:
        table = finance.STK_ML_QUOTA  # 市场通成交与额度信息
        q = query(
            table.day, table.quota_daily, table.quota_daily_balance
        ).filter(
            table.link_id.in_(['310001', '310002']), table.day <= i  # 沪股通、深股通
        ) \
            .order_by(table.day.desc()) \
            .limit(70)

        money_df = finance.run_query(q)
        money_df['net_amount'] = money_df['quota_daily'] - money_df['quota_daily_balance']  # 每日额度-每日剩余额度=净买入额
        # 分组求和
        money_df = money_df.groupby('day')[['net_amount']].sum().iloc[-WINDOW:]  # 过去g.window天求和
        mid = money_df['net_amount'].mean()
        stdev = money_df['net_amount'].std()
        upper = mid + STDEV_N * stdev
        lower = mid - STDEV_N * stdev
        mf = money_df['net_amount'].iloc[-1]

        _DT.append(i)
        _mfs.append(mf)
        _UP.append(upper)
        _DW.append(lower)
        _MiD.append(mid)

    return _DT, _mfs, _UP, _DW, _MiD


def main():
    auth("13516771087", "www1995com")
    print(get_query_count())
    pre_date = (datetime.date.today() - datetime.timedelta(1)).strftime('%Y-%m-%d')
    # pre_date = datetime.datetime(year=2016, month=4, day=1).strftime('%Y-%m-%d')
    dts, mfs, ups, dws, mids = get_boll(pre_date)

    pl.title("North Money Band")
    pl.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    pl.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    pl.plot(dts, mids, "y", lw=0.5)
    pl.plot(dts, ups, "r", lw=0.5)
    pl.plot(dts, dws, "g", lw=0.5)
    pl.plot(dts, mfs, lw=1)
    pl.show()


if __name__ == '__main__':
    main()
