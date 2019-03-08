# coding=utf-8

import inspect
import os
import warnings
from importlib import import_module
from wsgiref.simple_server import make_server, WSGIServer

import select
from itsdangerous import URLSafeSerializer

from kalos import __kalos__
from kalos.mime import Suffix_mime
from kalos.request import Request, request_local
from kalos.response import WrapperResponse, Response, wrap_response
from kalos.router import Router
from kalos.session import Session, session_local
from kalos.static import StaticFile
from kalos.utils import Env
from kalos.verb import Verb


class KalosServer(WSGIServer, object):

    def serve_forever_bsd(self, max_events=1000):
        kqueue = select.kqueue()
        kevents = [select.kevent(self.socket.fileno(), filter=select.KQ_FILTER_READ, flags=select.KQ_EV_ADD)]
        index = 0
        request_addr = dict()
        while True:
            events = kqueue.control(kevents, max_events)
            for event in events:
                # socket进来，将event加入监听
                if event.ident == self.socket.fileno():
                    request, client_address = self.socket.accept()
                    index += 1
                    request_addr[index] = (request, client_address)
                    kevents.append(select.kevent(request.fileno(), filter=select.KQ_FILTER_READ, flags=select.KQ_EV_ADD, udata=index))
                elif event.filter == select.KQ_FILTER_READ and event.udata > 0 and event.flags == select.KQ_EV_ADD:
                    try:
                        kevents.remove(
                            select.kevent(request_addr[event.udata][0].fileno(),
                                          filter=select.KQ_FILTER_READ, flags=select.KQ_EV_ADD, udata=event.udata))
                    except Exception as e:
                        pass
                    # t = Thread(target=self._handle_request_noblock_bsd, args=request_addr[event.udata])
                    self._handle_request_noblock_bsd(*request_addr[event.udata])
                    #t.setDaemon(True)
                    #t.run()

    def serve_forever(self, poll_wait=0.5):
        if os.uname()[0] == "Darwin":
            self.serve_forever_bsd()
        else:
            super(KalosServer, self).serve_forever(poll_wait)

    def _handle_request_noblock_bsd(self, request, client_address):
        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
        else:
            self.shutdown_request(request)


class Kalos(object):
    """
    A simple http framework
    :param static_dir: 静态文件目录
    :param template_dir: 模版目录
    :param: app_file: app实例所在文件
    """

    def __init__(self, name="Kalos", static_dir="static", template_dir="template", app_file=""):
        self.name = name
        self.static_dir = static_dir
        self.template_dir = template_dir
        self._SessionInterface = Session  # session处理类，可以重写
        self.app_env = Env(name)  # 应用环境变量
        self._safe_serializer = URLSafeSerializer(self.app_env.SECRET_KEY, self.app_env.SALT)
        self.before_request_funcs = []  # 在请求处理之前调用
        self.after_request_funcs = []  # 请求处理完，返回response之前调用
        self.app_error_handlers = dict()  # http 错误代码处理映射
        self.app_file = app_file

    @property
    def static_server(self):
        return StaticFile(self)

    @property
    def static_path(self):
        """静态文件目录和app定义的文件在同一个目录下面"""
        return os.sep.join([os.path.dirname(os.path.abspath(self.app_file)), self.static_dir])

    @property
    def template_path(self):
        """模板文件目录应该和app定义在同一个目录下面"""
        return os.sep.join([os.path.dirname(os.path.abspath(self.app_file)), self.template_dir])

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
        :param environment:
        :param start_response:
        """
        request = Request(environment)
        # 将request放入request_local
        request_local.put("request", request)
        opened_session = self._SessionInterface().open_session(self, request)
        session_local.put("session", opened_session)
        session_local.put("app", self)
        for f in self.before_request_funcs:
            try:
                f()
            except Exception as e:
                warnings.warn(e, RuntimeWarning)
        # 处理静态文件
        if "." in request.path_info and request.path_info.split(".")[-1] in Suffix_mime:
            response = self.static_server(request, request.path_info)
        else:
            router = Router(url=request.path_info, methods=request.method)
            r, handler = self.find_router_handler(router)
            # 处理404
            if handler is None:
                response = Response(status=404)
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
        session_local.remove("app")
        return wrapper_resp()

    @property
    def routers(self):
        return self.__class__.__router_map__

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def run(self, host="127.0.0.1", port=10101):
        server = make_server(host, port, self.wsgi_app, server_class=KalosServer)
        print("{} is listening {}:{}".format(self.name, host, port))
        print("\033[1;32;40m")
        print(__kalos__)
        print("\033[0m")
        print("Routers list:\n{}".format("\n".join(map(lambda x: repr(x), self.routers.keys()))))
        server.serve_forever()
