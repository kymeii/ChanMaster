# coding=utf-8

from __future__ import absolute_import

__author__ = "hanweiwei"
__date__ = "2020/10/13"

from jqdatasdk import *

if __name__ == '__main__':
    auth('13516771087', 'www1995com')
    print get_query_count()