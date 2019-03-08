# coding=utf-8

import json

from kalos.registry import Roselle
from kalos.request import request
import time
from kalos.session import session

ros = Roselle(__file__)


@ros.register_app_error_handler(401)
@ros.register_app_error_handler(404)
def handle(code):
    if code == 401:
        msg = "未授权"
    elif code == 404:
        msg = "资源未找到"
    else:
        msg = "未知错误"
    return json.dumps({
        "code": code,
        "msg": msg
    }), code


@ros.register_before_request
def before_request():
    request.start_time = time.time() * 1000
    session["name"] = "hello kalos"


@ros.register_after_request
def after_request(resp):
    now = time.time() * 1000
    print "spend %f ms" % (now - request.start_time)
    print session["name"]
    return resp