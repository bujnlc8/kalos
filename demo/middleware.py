# coding=utf-8

import json

from kalos.registry import Roselle
from kalos.request import request
import time
from kalos.session import session

ros = Roselle(__file__)


@ros.register_app_error_handler(401)
def handle(code):
    return json.dumps({
        "code": 401,
        "msg": "未授权"
    }), 401


@ros.register_before_request
def before_request():
    request.start_time = time.time()
    session["name"] = "hello kalos"


@ros.register_after_request
def after_request(resp):
    now = time.time()
    print "spend %f" % (now - request.start_time)
    print session["name"]
    return resp