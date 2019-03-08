# coding=utf-8

import functools
import warnings

from kalos.response import wrap_response
from kalos.router import Router
from kalos.utils import wrapper_pangolin
from kalos.verb import Verb


class Roselle(object):
    """
    `洛神`，负责view和middleware的注册
    """

    def __init__(self, name):
        self.name = name
        self.__router_map__ = {}
        self.__app_error_handlers__ = {}
        self.__before_request__ = []
        self.__after_request__ = []

    def route(self, url="/", group="", methods=None):
        def wrapper(func):
            @functools.wraps(func)
            def inner_wrapper(*args, **kwargs):
                def inner_inner_wrapper(*args, **kwargs):
                    resp = wrap_response(func, *args, **kwargs)
                    return resp

                return inner_inner_wrapper(*args, **kwargs)

            # 弥补wrapper之后签名改变的问题
            inner_wrapper = wrapper_pangolin(inner_wrapper, func)
            new_group, new_url, new_methods = group, url, methods
            if new_group and new_group.startswith("/"):
                new_group = new_group[1:]
            if new_url:
                if not new_url.startswith("/"):
                    new_url = "/" + new_url
                    warnings.warn("url should startswith `\\`", SyntaxWarning)
            if not new_methods:
                new_methods = [Verb.GET]
            else:
                if type(new_methods) is not list:
                    new_methods = [new_methods.upper()]
                else:
                    new_methods = map(lambda x: x.upper(), new_methods)
                for m in new_methods:
                    if m not in Verb.__slots__:
                        msg = 'do not support method {}'.format(m)
                        raise Exception(msg)
            router = Router(new_group, new_url, new_methods)
            if router in self.__router_map__:
                msg = "duplicate router {}".format(router)
                raise Exception(msg)
            self.__router_map__[router] = inner_wrapper
            return inner_wrapper

        return wrapper

    def register_app_error_handler(self, error_no):
        """
        注册http错误码处理
        """

        def recoder(f):
            self.__app_error_handlers__[error_no] = f
            return f

        return recoder

    def register_before_request(self, f):
        self.__before_request__.append(f)
        return f

    def register_after_request(self, f):
        self.__after_request__.append(f)
        return f