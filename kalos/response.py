# coding=utf-8

import functools
import os

from kalos import __version__
from kalos.mime import MIME
from kalos.session import current_user, app
from kalos.template import Template
from kalos.utils import cookie_date, wrapper_pangolin


class StatusCode(object):
    """
    http状态码
    see: https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
    """

    def __init__(self, status):
        self.status = status

    _status_code = {
        100: "100 Continue",
        101: "101 Switching Protocols",
        102: "102 Processing",
        103: "103 Early Hints",
        200: "200 OK",
        201: "201 Created",
        202: "202 Accepted",
        203: "203 Non-Authoritative Information",
        204: "204 No Content",
        205: "205 Reset Content",
        206: "206 Partial Content",
        207: "207 Multi-Status",
        208: "208 Already Reported",
        226: "226 IM Used",
        300: "300 Multiple Choices",
        301: "301 Moved Permanently",
        302: "302 Found (Previously \"Moved temporarily\")",
        303: "303 See Other",
        304: "304 Not Modified",
        305: "305 Use Proxy",
        306: "306 Switch Proxy",
        307: "307 Temporary Redirect",
        308: "308 Permanent Redirect",
        400: "400 Bad Request",
        401: "401 Unauthorized",
        402: "402 Payment Required",
        403: "403 Forbidden",
        404: "404 Not Found",
        405: "405 Method Not Allowed",
        406: "406 Not Acceptable",
        407: "Proxy Authentication Required",
        408: "Request Timeout",
        409: "409 Conflict",
        410: "410 Gone",
        411: "411 Length Required",
        412: "412 Precondition Failed",
        413: "413 Payload Too Large",
        414: "414 URI Too Long",
        415: "415 Unsupported Media Type",
        416: "416 Range Not Satisfiable",
        417: "417 Expectation Failed",
        429: "429 Too Many Requests",
        500: "500 Internal Server Error",
        501: "501 Not Implemented",
        502: "502 Bad Gateway",
        503: "503 Service Unavailable",
        504: "504 Gateway Timeout",
        505: "505 HTTP Version Not Supported",
        999: "999 HTTP Code Not Supported"
    }

    def __repr__(self):
        if self.status in self._status_code:
            return self._status_code[self.status]
        return self._status_code[999]

    def __str__(self):
        return self.__repr__()


class Response(object):
    """
    通用response封装
    :param data: response data
    :param status: response status
    :param content_type: response status
    :param kwargs: they will all be input in header
    """

    def __init__(self, data="", status=200, content_type=MIME.Json, **kwargs):
        self.data = data
        self.status = status
        self.content_type = content_type
        self.length = len(self.data)
        self.headers = [("X-Web-Framework", "Kalos/{}".format(__version__))]
        self.headers.append(("Content-Type", content_type))
        for k, v in kwargs.iteritems():
            self.headers.append((k, v))

    def __call__(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
            self.headers.append((k, v))
        return repr(StatusCode(self.status)), self.headers


def make_redirect(code=302, location="", response=None):
    """
    生成重定向跳转
    :param code: 302,301...
    :param location: location to redirect
    :param response: A Response object
    :return: response
    """
    if response is not None:
        if not isinstance(response, Response):
            raise Exception("response must be a Response object")
        response.status = code
        response.headers.append(("Location", location))
        return response
    else:
        response = Response(status=code, Location=location)
        return response


class WrapperResponse(object):
    def __init__(self, response, start_response):
        self.response = response
        self.start_response = start_response

    def __call__(self, *args, **kwargs):
        self.start_response(*self.response())
        return [self.response.data]

    def set_cookie(self, kvs, max_age=3600 * 24 * 7, expires=None, domain=None, path="/", http_only=True):
        cookies = [kvs]
        cookies.append("Max-Age=%s" % max_age)
        if expires:
            cookies.append("Expires=%s" % cookie_date(expires))
        if domain:
            cookies.append("Domain=%s" % domain)
        if path:
            cookies.append("Path=%s" % path)
        if http_only:
            cookies.append("HttpOnly")

        self.response.headers.append(("Set-Cookie", "; ".join(cookies)))

    def set_header(self, key, value):
        self.response.append((key, value))

    def __getattr__(self, item):
        return getattr(self.response, item)


def wrap_response(func, *args, **kwargs):
    response = func(*args, **kwargs)
    if (type(response) is tuple or type(response) is list) and len(response) > 1:
        # 第一位为返回的数据， 第二为http code
        resp = response[0]
        http_code = response[1]
        if isinstance(resp, Response):
            resp.status = http_code
        else:
            resp = Response(data=resp, status=http_code)
    else:
        if not isinstance(response, Response):
            resp = Response(data=response)
        else:
            resp = response
    return resp


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not (current_user and current_user.is_login):
            return Response(status=401)
        else:
            return func(*args, **kwargs)

    return wrapper_pangolin(wrapper, func)


def render_template(tpl, *args, **context):
    """
    渲染模版引擎， 返回html
    :param tpl: 以tpl或html结尾的文件, 否则认为是模版字符串
    :param context:
    :return: response
    """
    text = []
    if tpl.endswith(".tpl") or tpl.endswith(".html"):
        full_path = os.sep.join([app.template_path, tpl])
        try:
            with open(full_path, 'r') as f:
                for x in f:
                    text.append(x)
        except IOError as e:
            raise e
    else:
        text = [tpl]
    tpl = Template("".join(text))
    data = tpl.render(*args, **context)
    resp = Response(data=data, content_type=MIME.Html)
    return resp