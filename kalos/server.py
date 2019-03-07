# coding=utf-8

import inspect
import os
import select
import warnings
from importlib import import_module
from wsgiref.simple_server import make_server, WSGIServer

from itsdangerous import URLSafeSerializer

from kalos import __kalos__
from kalos.request import Request, request_local
from kalos.response import response_404, WrapperResponse, Response, wrap_response
from kalos.router import Router
from kalos.session import Session, session_local
from kalos.utils import Env
from kalos.verb import Verb


class KalosServer(WSGIServer, object):
    def serve_forever_bsd(self, max_events=2000):
        kqueue = select.kqueue()
        kevents = [select.kevent(self.socket.fileno(), filter=select.KQ_FILTER_READ,
                                 flags=select.KQ_EV_ADD)]
        while True:
            events = kqueue.control(kevents, max_events)
            for event in events:
                if event.filter == select.KQ_FILTER_READ:
                    self._handle_request_noblock()

    def serve_forever(self, poll_wait=0.5):
        if os.uname()[0] == "Darwin":
            self.serve_forever_bsd()
        else:
            super(KalosServer, self).serve_forever(poll_wait)


class Kalos(object):
    """
    A simple http framework
    """

    def __init__(self, name="Kalos", static_dir="static", template_dir="template"):
        self.name = name
        self.static_dir = static_dir
        self.template_dir = template_dir
        self._SessionInterface = Session  # session处理类，可以重写
        self.app_env = Env(name)  # 应用环境变量
        self._safe_serializer = URLSafeSerializer(self.app_env.SECRET_KEY, self.app_env.SALT)
        self.before_request_funcs = []  # 在请求处理之前调用
        self.after_request_funcs = []  # 请求处理完，返回response之前调用
        self.app_error_handlers = dict()  # http 错误代码处理映射

    def register_roselle(self, path):
        """
        注册view或中间件
        :param path: 模块绝对路径
        :return:
        """
        paths = path.split(":")
        if len(paths) == 1:
            module_path = paths[0]
            roselle_name = "ros"
        elif len(paths) > 1:
            module_path = paths[0]
            roselle_name = paths[1]
        else:
            raise Exception("register failed, the path is wrong")
        m = import_module(module_path)
        ros = getattr(m, roselle_name)
        # 注册路由
        for router, func in ros.__router_map__.iteritems():
            if self.find_router_handler(router)[0]:
                msg = "duplicate router {}".format(router)
                raise Exception(msg)
            else:
                self.__class__.__router_map__[router] = func

        # 注册__app_error_handlers__
        for code, func in ros.__app_error_handlers__.iteritems():
            self.app_error_handlers[code] = func

        # 注册before_request
        for func in ros.__before_request__:
            self.before_request_funcs.append(func)

        # 注册after_request
        for func in ros.__after_request__:
            self.after_request_funcs.append(func)

    __router_map__ = {}

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
        for f in self.before_request_funcs:
            try:
                f()
            except Exception as e:
                warnings.warn(e, RuntimeWarning)
        router = Router(url=request.path_info, methods=request.method)
        r, handler = self.find_router_handler(router)
        # 处理404
        if handler is None:
            response = response_404
        elif request.method == Verb.OPTIONS:  # 处理OPTIONS
            response = Response(Allow=",".join(r.methods))
        else:
            # 解析url中的变量，放入handler
            variables = []
            if r.has_variable:
                variables = r.get_variable_list(request.path_info)
            argspec = inspect.getargspec(handler.__origin_func__)
            if len(argspec.args) == 0:
                response = handler()
            else:
                if argspec.args[0] == "request":
                    response = handler(request, *variables)
                else:
                    response = handler(*variables)
        # 调用错误码处理方法
        handle_error_func = self.app_error_handlers.get(response.status)
        if handle_error_func and callable(handle_error_func):
            response = wrap_response(handle_error_func, response.status)
        wrapper_resp = WrapperResponse(response, start_response)
        opened_session.save_session(self, wrapper_resp)
        for f in self.after_request_funcs:
            try:
                wrapper_resp = f(wrapper_resp)
            except Exception as e:
                warnings.warn(e, RuntimeWarning)
        request_local.remove("request")
        session_local.remove("session")
        return wrapper_resp()

    @property
    def routers(self):
        return self.__class__.__router_map__

    def run(self, host="127.0.0.1", port=10101):
        server = make_server(host, port, self.wsgi_app, server_class=KalosServer)
        print("{} is listening {}:{}".format(self.name, host, port))
        print("\033[1;32;40m")
        print(__kalos__)
        print("\033[0m")
        print("Routers list:\n{}".format("\n".join(map(lambda x: repr(x), self.routers.keys()))))
        server.serve_forever()
