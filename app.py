# coding=utf-8
import sys

reload(sys)
sys.setdefaultencoding("utf8")
import logging

__author__ = "hanweiwei"
__date__ = "2018/10/24"

app_log = logging.getLogger("app")
app_log.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=None)
formatter = logging.Formatter('%(asctime)s  %(filename)s : %(levelname)s  %(message)s')  #定义该handler格式
handler.setFormatter(formatter)
app_log.addHandler(handler)
