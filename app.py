# coding=utf-8

import logging

from chan.chan_app import ChanApp
from chan.level import FiveMinuteLevel, OneMinuteLevel
from gateway.jq.jq_gateway import JQGateway
from gateway.tq.tq_gateway import TQGateway
from trader.constant import Exchange

__author__ = "hanweiwei"
__date__ = "2018/10/24"

app_log = logging.getLogger("app")
app_log.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=None)
formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')  # 定义该handler格式
handler.setFormatter(formatter)
app_log.addHandler(handler)

if __name__ == '__main__':
    chan_app = ChanApp(FiveMinuteLevel(), JQGateway, Exchange.AGU, "300253.XSHE")
    chan_app.start()
