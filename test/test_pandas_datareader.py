# coding=utf-8
import datetime
import pandas_datareader as pdr
import requests_cache
from pandas_datareader.yahoo.fx import YahooFXReader
# from pandas_datareader.tests.yahoo import test_yahoo

expire_after = datetime.timedelta(days=3)
session = requests_cache.CachedSession(cache_name='cache', backend='sqlite', expire_after=expire_after)

__author__ = "hanweiwei"
__date__ = "2018/10/24"

if __name__ == '__main__':
    # print pdr.get_data_yahoo('600797.SS', session=session)
    yfr = YahooFXReader("601788.SS",interval="1m")
    print yfr.read()
    # test_yahoo.