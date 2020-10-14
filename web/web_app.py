# coding=utf-8
from typing import List

from chan.db.dao import ChanBarDataDao, PenDao, CentreDao
from chan.db.object import ChanBarDataDO
from chan.level import FiveMinuteLevel, parse_level
from tools import time_tools
from trader.constant import Exchange, Interval
from web.encoder.alchemy_encoder import AlchemyEncoder
from flask_cors import CORS
from flask import request

__author__ = "hanweiwei"
__date__ = "2019-06-07"

from flask import Flask, json

app = Flask(__name__)
CORS(app)
app.json_encoder = AlchemyEncoder
chan_bar_data_dao = ChanBarDataDao()
pen_dao = PenDao()
centre_dao = CentreDao()


@app.route('/kline', methods=['GET'])
def kline():
    interval = request.args.get('interval', '5m')

    minute_level = parse_level(interval)
    secure = "300253.XSHE"
    bars: List[ChanBarDataDO] = chan_bar_data_dao.select("JQ", Exchange.AGU.value, secure,
                                                         minute_level.get_level().value,
                                                         10000)
    pens = pen_dao.select("JQ", Exchange.AGU.value, secure, minute_level.get_level().value,
                          bars[0].datetime)
    sub_pens = pen_dao.select("JQ", Exchange.AGU.value, secure, minute_level.get_child_level().value,
                              bars[0].datetime)
    sub_centres = centre_dao.select("JQ", Exchange.AGU.value, secure, minute_level.get_level().value,
                                    bars[0].datetime)
    for pen in sub_pens:
        if pen.interval == "1m":
            pen.start_datetime = time_tools.m1_2_m5(pen.start_datetime)
            pen.end_datetime = time_tools.m1_2_m5(pen.end_datetime)
        else:
            pen.start_datetime = time_tools.m5_2_m30(pen.start_datetime)
            pen.end_datetime = time_tools.m5_2_m30(pen.end_datetime)

    for centre in sub_centres:
        if centre.interval == "1m":
            centre.start_datetime = time_tools.m1_2_m5(centre.start_datetime)
            centre.end_datetime = time_tools.m1_2_m5(centre.end_datetime)
        else:
            centre.start_datetime = time_tools.m5_2_m30(centre.start_datetime)
            centre.end_datetime = time_tools.m5_2_m30(centre.end_datetime)

    return json.dumps({
        "pens": pens,
        "bars": bars,
        "sub_pens": sub_pens,
        "sub_centres": sub_centres
    })


def run_web_app():
    app.run()


if __name__ == '__main__':
    run_web_app()
