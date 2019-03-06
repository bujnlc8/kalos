# coding=utf-8

import functools
import inspect
import warnings
from wsgiref.simple_server import make_server

from itsdangerous import URLSafeSerializer

from kalos import __kalos__
from kalos.request import Request, request_local
from kalos.response import response_404, WrapperResponse, Response, wrap_response
from kalos.router import Router
from kalos.session import Session, session_local
from kalos.utils import Env, wrapper_pangolin
from kalos.verb import Verb


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
        self.before_request_funcs = []  # 在请求处理之前调用
        self.after_request_funcs = []  # 请求处理完，返回response之前调用
        self.before_handler_funcs = []  # 在handler调用之前调用
        self.after_handler_funcs = []   # 在handler调用之后调用
        self.app_error_handlers = dict()  # http 错误代码处理映射
    
    def register_app_error_handler(self, error_no):
        """
        注册http错误码处理
        """
        def recoder(f):
            self.app_error_handlers[error_no] = f
            return f
        return recoder

    def register_before_request(self, f):
        """
        注册请求处理之前调用的方法, 没有参数
        :param f:
        :return:f:
        """
        self.before_request_funcs.append(f)
        return f

    def register_after_request(self, f):
        """
        注册请求处理完，返回response之前调用的方法, 参数为response对象
        :param f:
        :return:f:
        """
        self.after_request_funcs.append(f)
        return f

    def register_before_handle(self, f):
        """
        注册在handler调用之前调用的方法
        :param f:
        :return:f:
        """
        self.before_handler_funcs.append(f)
        return f

    def register_after_handle(self, f):
        """
        注册在handler调用之后调用的方法
        :param f:
        :return:f:
        """
        self.after_handler_funcs.append(f)
        return f

    def __register__(self, path):
        __import__(path)

    __router_map__ = {}

    def route(self, group="", url="/", methods=None):
        def wrapper(func):
            @functools.wraps(func)
            def inner_wrapper(*args, **kwargs):
                def inner_inner_wrapper(*args, **kwargs):
                    for f in self.before_handler_funcs:
                        try:
                            f()
                        except Exception as e:
                            warnings.warn(e, RuntimeWarning)
                    resp = wrap_response(func, *args, **kwargs)
                    # 包装成
                    for f in self.after_handler_funcs:
                        try:
                            f()
                        except Exception as e:
                            warnings.warn(e, RuntimeWarning)
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
            if self.find_router_handler(router)[0]:
                msg = "duplicate router {}".format(router)
                raise Exception(msg)
            else:
                self.__class__.__router_map__[router] = inner_wrapper
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
            response = wrap_response(handle_error_func)
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
        server = make_server(host, port, self.wsgi_app)
        print("{} is listening {}:{}".format(self.name, host, port))
        print("\033[1;32;40m")
        print(__kalos__)
        print("\033[0m")
        print("Routers list:\n{}".format("\n".join(map(lambda x: repr(x), self.routers.keys()))))
        server.serve_forever()