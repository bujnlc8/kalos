# coding=utf-8

import json
import urllib

from kalos.mime import MIME


class Request(object):
    """
    request封装
    """
    def __init__(self, environment):
        self._environment = environment
        # 1.0.0.127.in-addr.arpa
        self.remote_host = self._environment["REMOTE_HOST"]
        # HTTP/1.1
        self.server_protocol = self._environment["SERVER_PROTOCOL"]
        # WSGIServer/0.1 Python/2.7.15
        self.server_software = self._environment["SERVER_SOFTWARE"]
        # GET
        self.method = self._environment["REQUEST_METHOD"]
        # a=1&b=2
        self.query_string = self._environment["QUERY_STRING"]
        # 1.0.0.127.in-addr.arpa
        self.server_name = self._environment["SERVER_NAME"]
        # 127.0.0.1
        self.remote_addr = self._environment["REMOTE_ADDR"]
        # 10101
        self.server_port = self._environment["SERVER_PORT"]
        # '8'
        self._content_length = self._environment["CONTENT_LENGTH"]
        # 8
        self.content_length = int(self._content_length) if self._content_length else 0
        # host
        self.http_host = self._environment["HTTP_HOST"]
        # */*
        self.http_accept = self._environment["HTTP_ACCEPT"]
        # (1, 0)
        self.wsgi_version = self._environment["wsgi.version"]
        # curl/7.54.0
        self.http_user_agent = self._environment["HTTP_USER_AGENT"]
        #  CGI/1.1
        self.gateway_interface = self._environment["GATEWAY_INTERFACE"]
        # False
        self.wsgi_run_once = self._environment["wsgi.run_once"]
        # True
        self.wsgi_multiprocess = self._environment["wsgi.multiprocess"]
        # text/plain
        self.content_type = self._environment["CONTENT_TYPE"]
        # http
        self.url_scheme = self._environment["wsgi.url_scheme"]
        # /abc
        self.path_info = self._environment["PATH_INFO"]
        # fileobject
        self.file = self._environment["wsgi.input"]

    @property
    def args(self):
        qs = urllib.unquote_plus(self.query_string)
        qss = qs.split("&")
        kv = {}
        for x in qss:
            xx = x.split("=")
            kv[xx[0]] = xx[1].decode("utf-8")
        qs_obj = QueryStrings(**kv)
        return qs_obj

    @property
    def bin(self):
        if hasattr(self, "_bin"):
            return self._bin
        else:
            self._bin = self.file.read(int(self.content_length))
        return self._bin

    @property
    def json(self):
        if self.content_type == MIME.Json:
            return json.loads(str(self.bin))


class QueryStrings(object):
    def __init__(self, **kwargs):
        self.__dict__["__qs_field__"] = []
        for k, v in kwargs.iteritems():
            self.__dict__[k] = v
            self.__dict__['__qs_field__'].append(k)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def keys(self):
        for x in self.__dict__["__qs_field__"]:
            yield x

    def get(self, key, d=None, m=None):
        if key not in self.keys():
            if d:
                return d
        else:
            if m is not None:
                return m(self[key].encode("utf-8"))
            else:
                return self[key]

    def __repr__(self):
        kv = {}
        for k in self.keys():
            kv[k] = self[k]
        return "{}".format(kv)