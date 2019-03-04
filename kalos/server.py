# coding=utf-8

import functools
import warnings
from wsgiref.simple_server import make_server

from kalos.request import Request
from kalos.router import Router
from kalos.verb import Verb


class Kalos(object):
    """
    A simple http framework
    """

    def __init__(self, name="Kalos", static_dir="static", template_dir="template"):
        self.name = name
        self.static_dir = static_dir
        self.template_dir = template_dir

    __router_map__ = {}

    def route(self, group="", url="/", methods=None):
        def wrapper(func):
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
            if self.find_router_handler(router):
                msg = "duplicate router {}".format(router)
                raise Exception(msg)
            else:
                self.__class__.__router_map__[router] = func

            @functools.wraps(func)
            def inner_wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return inner_wrapper

        return wrapper

    def find_router_handler(self, router):
        """find the router"""
        if set(router.methods).intersection({Verb.OPTIONS}):
            router.methods = Verb.__slots__
        if not isinstance(router, Router):
            raise Exception("the arg router must be a Router object")
        for r, v in self.__router_map__.iteritems():
            if r == router:
                return r, v

    def wsgi_app(self, environment, start_response):
        """
        目前仅处理api请求，忽略静态文件
        :param environment:
        :param start_response:
        """
        request = Request(environment)
        router = Router(url=request.path_info, methods=request.method)
        r, handler = self.find_router_handler(router)
        # 处理404
        if handler is None:
            start_response("404 NOT FOUND", [('Content-Type', 'application/json')])
            return [b""]
        elif request.method == Verb.OPTIONS: # 处理OPTIONS
            start_response("200 OK", [("Allow", ",".join(r.methods))])
            return [b""]
        # 解析url中的变量，放入handler
        variables = []
        if r.has_variable:
            variables = r.get_variable_list(request.path_info)
        response = handler(request, *variables)
        start_response("200 OK", [('Content-Type', 'text/plain')])
        return [response]

    @property
    def routers(self):
        return self.__class__.__router_map__

    def run(self, host="127.0.0.1", port=10101):
        server = make_server(host, port, self.wsgi_app)
        print "{} is listening {}:{}".format(self.name, host, port)
        print "Routers list:\n{}".format("\n".join(map(lambda x: repr(x), self.routers.keys())))
        server.serve_forever()
