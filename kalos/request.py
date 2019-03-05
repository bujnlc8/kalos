# coding=utf-8

import json
import urllib
from cgi import parse_header, parse_multipart, escape

from kalos.local import Local
from kalos.mime import MIME
from kalos.utils import ImmutableDict

_header_list = {
    "SERVER_PROTOCOL": "PROTOCOL",
    "SERVER_SOFTWARE": "SERVER_SOFTWARE",
    "REQUEST_METHOD": "METHOD",
    "SERVER_NAME": "SERVER_NAME",
    "REMOTE_ADDR": "REMOTE_ADDR",
    "SERVER_PORT": "SERVER_PORT",
    "CONTENT_LENGTH": "CONTENT_LENGTH",
    "HTTP_HOST": "HOST",
    "HTTP_USER_AGENT": "USER_AGENT",
    "CONTENT_TYPE": "CONTENT_TYPE",
    "PATH_INFO": "PATH_INFO",
    "REMOTE_HOST": "REMOTE_HOST",
    "HTTP_COOKIE": "COOKIE"
}


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
        self._content_type = self._environment["CONTENT_TYPE"]
        self.content_type =  parse_header(self._content_type)[0]
        # http
        self.url_scheme = self._environment["wsgi.url_scheme"]
        # /abc
        self.path_info = self._environment["PATH_INFO"]
        # fileobject
        self.file = self._environment["wsgi.input"]

    @property
    def headers(self):
        head = {}
        for k, v in self._environment.iteritems():
            if k in _header_list.keys():
                head[_header_list[k]] = v
            else:
                if k.startswith("HTTP_"):
                    remove_underline = k[5:].replace("_", "-")
                    head[remove_underline] = v
        return ImmutableDict(**head)

    @property
    def cookie(self):
        c = Cookie(self.headers.get("COOKIE", ""))
        return c

    @property
    def args(self):
        qs = urllib.unquote_plus(self.query_string)
        qss = qs.split("&")
        kv = {}
        for x in qss:
            xx = x.split("=")
            kv[xx[0]] = escape(xx[1].decode("utf-8"))
        qs_obj = FieldStorage(**kv)
        return qs_obj

    @property
    def data(self):
        if hasattr(self, "_data"):
            return self._data
        else:
            self._data = self.file.read(int(self.content_length))
        return self._data

    @property
    def json(self):
        if self.content_type == MIME.Json:
            return json.loads(str(self.data))

    @property
    def form(self):
        ctype, pdict = parse_header(self._content_type)
        if ctype == MIME.Multipart:
            partdict = parse_multipart(self.file, pdict)
            return FieldStorage(**partdict)
        elif ctype == MIME.Form:
            form_obj = urllib.unquote_plus(str(self.data))
            form_obj = form_obj.split("&")
            kv = {}
            for x in form_obj:
                xx = x.split("=")
                kv[xx[0]] = escape(xx[1].decode("utf-8"))
            return FieldStorage(**kv)
        else:
            return FieldStorage()


class FieldStorage(object):
    def __init__(self, **kwargs):
        self.__dict__["__s_field__"] = []
        for k, v in kwargs.iteritems():
            self.__dict__[k] = v
            self.__dict__['__s_field__'].append(k)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def keys(self):
        for x in self.__dict__["__s_field__"]:
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


request_local = Local()

request = request_local("request")


class Cookie(object):
    """
    Cookie封装
    :param line: 最原始的cookie
    """
    def __init__(self, line):
        object.__setattr__(self, "__origin_cookie__", line)
        object.__setattr__(self, "__cookie__dict__", {})
        if line:
            split_items = line.split("; ")
            for item in split_items:
                key, value = item.split("=")
                setattr(self, key, value)

    def __iter__(self):
        for k, v in self.__cookie__dict__.iteritems():
            yield k,v

    def __setattr__(self, key, value):
        self.__cookie__dict__[key] = value

    def __getattr__(self, item):
        return self.__cookie__dict__[item]

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __call__(self, name):
        return self[name]

    def get(self, name):
        try:
            return self[name]
        except KeyError:
            return ""