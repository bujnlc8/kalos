# coding=utf-8

from kalos.registry import Roselle

ros = Roselle(__file__)


@ros.route(group="book", url="/<:id|int>", methods="GET")
def get_book(id):
    return "", 401