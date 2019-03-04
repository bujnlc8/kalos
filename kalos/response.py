# coding=utf-8

from kalos import __version__
from kalos.mime import MIME


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
        self.headers = [("X-Web-Framework", "Kalos/{}".format(__version__))]
        self.headers.append(("Content-Type", content_type))
        for k, v in kwargs.iteritems():
            self.headers.append((k, v))

    def __call__(self, *args, **kwargs):
        for k, v in kwargs.iteritems():
            self.headers.append((k, v))
        return repr(StatusCode(self.status)), self.headers


response_200 = Response()

response_404 = Response(data="kalos is missing...", status=404)

response_401 = Response(data="You are not certification", status=401)


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