# coding=utf-8

from abc import ABCMeta, abstractmethod

from kalos.local import Local


class SessionInterface(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def open_session(self, request):
        raise NotImplementedError

    @abstractmethod
    def save_session(self, response):
        raise NotImplementedError


class Session(SessionInterface):

    def __init__(self):
        object.__setattr__(self, "__ss__", {})

    def __setattr__(self, key, value):
        self.__ss__.update({
            key: value
        })

    def __getattr__(self, item):
        return self.__ss__[item]

    def __setitem__(self, key, value):
        self.__ss__.update({
            key: value
        })

    def __getitem__(self, item):
        return self.__ss__[item]

    def open_session(self, request):
        cookie = request.headers.get("COOKIE")
        if cookie:
            s = Session()
            s["COOKIE"] = cookie
            return s
        else:
            s = Session()
            s["COOKIE"] = "no_cookie"
            return s

    def save_session(self, response):
        return response

    def __repr__(self):
        return str(self.__ss__)


session_local = Local()

session = session_local("session")
