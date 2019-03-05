# coding=utf-8

import functools
from abc import ABCMeta, abstractmethod, abstractproperty

from datetime import datetime, timedelta

from kalos.response import response_401
from kalos.utils import Proxy, wrapper_pangolin, Local


class UserABC(object):
    __metaclass__ = ABCMeta

    def __init__(self, id_, is_login=True):
        self.id_ = id_
        self._is_login = is_login

    @abstractmethod
    def login(self):
        raise NotImplementedError

    @abstractmethod
    def logout(self):
        raise NotImplementedError

    @abstractproperty
    def is_login(self):
        raise NotImplementedError


class UserMixin(UserABC):

    def __init__(self, id_, is_login=True):
        super(UserMixin, self).__init__(id_, is_login)

    def login(self):
        self._is_login = True

    def logout(self):
        self._is_login = False

    @property
    def is_login(self):
        return self._is_login


anonymous_user = UserMixin(0, False)


class SessionInterface(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def open_session(self, app, request):
        raise NotImplementedError

    @abstractmethod
    def save_session(self, app, response):
        raise NotImplementedError

    def __init__(self):
        object.__setattr__(self, "__ss__", {})

    def __setattr__(self, key, value):
        self.__ss__.update({
            key: value
        })

    def __getattr__(self, item):
        try:
            return self.__ss__[item]
        except KeyError:
            return None

    def __setitem__(self, key, value):
        self.__ss__.update({
            key: value
        })

    def __getitem__(self, item):
        try:
            return self.__ss__[item]
        except KeyError:
            return None


class Session(SessionInterface):
    """
    默认取cookie中的session字段，也可以自己实现
    """

    def open_session(self, app, request):
        _session = request.cookie.get("session")
        s = Session()
        if _session:
            decode_str = app._safe_serializer.loads(_session)
            if decode_str["expire_time"] < datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
                s["user"] = anonymous_user
            else:
                if decode_str["id_"] == 0:
                    user = anonymous_user
                else:
                    user = UserMixin(decode_str["id_"])
                s["user"] = user
        else:
            s["user"] = anonymous_user
        return s

    def save_session(self, app, response):
        s = ""  # 表示加密后的session
        if current_user and current_user.is_login:
            # 让用户下线
            current_user.logout()
            user_dict = {
                "id_": current_user.id_,
                "expire_time": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
            }
            s = app._safe_serializer.dumps(user_dict)
        s = "session=%s" % s
        response.set_cookie(
            s,
            expires=datetime.now() + timedelta(days=7) - timedelta(seconds=10),
            domain=app.app_env.get("COOKIE_DOMAIN", ""))
        return response

    def __repr__(self):
        return str(self.__ss__)


session_local = Local()

session = session_local("session")

current_user = Proxy(lambda: session, "user")


def login_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not (current_user and current_user.is_login):
            return response_401
        else:
            return func(*args, **kwargs)

    return wrapper_pangolin(wrapper, func)
