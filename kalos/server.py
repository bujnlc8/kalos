# coding=utf-8

import functools
import inspect
import warnings
from wsgiref.simple_server import make_server

from kalos import __kalos__
from kalos.request import Request, request_local
from kalos.response import response_404, WrapperResponse, Response
from kalos.router import Router
from kalos.session import Session, session_local
from kalos.verb import Verb
from kalos.utils import Env
from itsdangerous import URLSafeSerializer


class Kalos(object):
    """
    A simple http framework
    """

    def __init__(self, name="Kalos", static_dir="static", template_dir="template"):
        self.name = name
        self.static_dir = static_dir
        self.template_dir = template_dir
        self._SessionInterface = Session  # session处理类，可以重写
        self.app_env = Env(name)   # 应用环境变量
        self._safe_serializer = URLSafeSerializer(self.app_env.SECRET_KEY, self.app_env.SALT)

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
            if self.find_router_handler(router)[0]:
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
        return None, None

    def wsgi_app(self, environment, start_response):
        """
        目前仅处理api请求，忽略静态文件
        :param environment:
        :param start_response:
        """
        request = Request(environment)
        # 将request放入request_local
        request_local.put("request", request)
        opened_session = self._SessionInterface().open_session(self, request)
        session_local.put("session", opened_session)
        router = Router(url=request.path_info, methods=request.method)
        r, handler = self.find_router_handler(router)
        # 处理404
        if handler is None:
            return WrapperResponse(response_404, start_response)()
        elif request.method == Verb.OPTIONS:  # 处理OPTIONS
            response = Response(Allow=",".join(r.methods))
            return WrapperResponse(response, start_response)()
        # 解析url中的变量，放入handler
        variables = []
        if r.has_variable:
            variables = r.get_variable_list(request.path_info)
        argspec = inspect.getargspec(handler)
        if len(argspec.args) == 0:
            response = handler()
        else:
            if argspec.args[0] == "request":
                response = handler(request, *variables)
            else:
                response = handler(*variables)
        if (type(response) is tuple or type(response) is list) and len(response) > 1:
            # 第一位为返回的数据， 第二为http code
            response1 = response[0]
            http_code = response[1]
            if isinstance(response1, Response):
                response1.status = http_code
                wrapper_resp = WrapperResponse(response1, start_response)
            else:
                response_wrap = Response(data=response1, status=http_code)
                wrapper_resp = WrapperResponse(response_wrap, start_response)
        else:
            if isinstance(response, Response):
                wrapper_resp = WrapperResponse(response, start_response)
            else:
                response_wrap = Response(data=response)
                wrapper_resp = WrapperResponse(response_wrap, start_response)
        opened_session.save_session(self, wrapper_resp)
        request_local.remove("request")
        session_local.remove("session")
        return wrapper_resp()

    @property
    def routers(self):
        return self.__class__.__router_map__

    def run(self, host="127.0.0.1", port=10101):
        server = make_server(host, port, self.wsgi_app)
        print("{} is listening {}:{}".format(self.name, host, port))
        print("\033[1;32;40m")
        print(__kalos__)
        print("\033[0m")
        print("Routers list:\n{}".format("\n".join(map(lambda x: repr(x), self.routers.keys()))))
        server.serve_forever()
