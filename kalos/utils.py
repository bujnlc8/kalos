# coding=utf-8

import os

from thread import get_ident


class Proxy(object):
    def __init__(self, func, name=None):
        object.__setattr__(self, "__func__", func)
        object.__setattr__(self, "__name__", name)

    @property
    def self(self):
        return getattr(self.__func__(), self.__name__)

    def __getattr__(self, item):
        return getattr(getattr(self.__func__(), self.__name__), item)

    def __setattr__(self, key, value):
        obj = getattr(self.__func__(), self.__name__)
        setattr(obj, key, value)
        setattr(self.__func__(), self.__name__, obj)

    def __setitem__(self, key, value):
        obj = getattr(self.__func__(), self.__name__)
        obj.__setitem__(key, value)
        setattr(self.__func__(), self.__name__, obj)

    def __getitem__(self, item):
        return getattr(self.__func__(), self.__name__).__getitem__(item)

    @property
    def __dict__(self):
        return getattr(self.__func__(), self.__name__).__dict__


class ImmutableDict(dict):
    """
    不可变dict
    """
    def __setitem__(self, key, value):
        raise TypeError("%r object does not support item assignment" % type(self).__name__)

    def __delitem__(self, key):
        raise TypeError("%r object does not support item deletion" % type(self).__name__)

    def __getattribute__(self, attribute):
        if attribute in ('clear', 'update', 'pop', 'popitem', 'setdefault'):
            raise AttributeError("%r object has no attribute %r" % (type(self).__name__, attribute))
        return dict.__getattribute__(self, attribute)

    def __hash__(self):
        return hash(tuple(sorted(self.iteritems())))

    def fromkeys(self, S, v=None):
        return type(self)(dict(self).fromkeys(S, v))


class Env(dict):
    """
    应用环境变量, 获取所有以`prefix.upper()_` 开头的环境变量
    """
    def __init__(self, prefix="kalos"):
        object.__setattr__(self, "__env_prefix__", prefix.upper())

        kvs = {}
        for k, v in os.environ.iteritems():
            if k.startswith(self.__env_prefix__):
                key = k[len(self.__env_prefix__) + 1:]
                if key in self.keys():
                    msg = "duplicate key {}".format(key)
                    raise KeyError(msg)
                kvs[key] = v
        super(Env, self).__init__(**kvs)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            return ""


def cookie_date(d):
    """
    转化成cookie expire格式
    :param d:
    :return:
    """
    d = d.utctimetuple()
    return '%s, %02d%s%s%s%s %02d:%02d:%02d GMT' % (
        ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')[d.tm_wday],
        d.tm_mday, "-",
        ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
         'Oct', 'Nov', 'Dec')[d.tm_mon - 1],
        "-", str(d.tm_year), d.tm_hour, d.tm_min, d.tm_sec
    )


def wrapper_pangolin(wrapper, wrapped):
    """
    装饰一个方法时，装饰后的方法的参数签名和原来不同不同，
    通过__origin__func__传递最原始的方法
    :param wrapper: 装饰方法
    :param wrapped: 被装饰方法
    :return:
    """
    if hasattr(wrapped, "__origin_func__"):
        wrapper.__origin_func__ = wrapped.__origin_func__
    else:
        wrapper.__origin_func__ = wrapped
    return wrapper

class Local(object):
    """
    实现一个线程安全的变量存取，主要是根据不同线程有不同的ident实现
    """

    def __init__(self):
        # self.__storage__ = {}  这样写会导致死循环
        object.__setattr__(self, "__storage__", {})

    def __setattr__(self, key, value):
        ident = get_ident()
        if ident in self.__storage__:
            exist_dict = self.__storage__[ident]
            exist_dict.update({
                key: value
            })
            self.__storage__[ident] = exist_dict
        else:
            new_dict = {key: value}
            self.__storage__[ident] = new_dict

    def __getattr__(self, item):
        ident = get_ident()
        if ident in self.__storage__:
            return self.__storage__[ident].get(item, None)
        else:
            return None

    def __delattr__(self, name):
        try:
            del self.__storage__[get_ident()][name]
            if not self.__storage__[get_ident()]:
                del self.__storage__[get_ident()]
        except KeyError:
            raise AttributeError(name)

    def __call__(self, name):
        def myself():
            return self

        return Proxy(myself, name)

    def put(self, name, item):
        self.__setattr__(name, item)

    def remove(self, name):
        self.__delattr__(name)