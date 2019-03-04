# coding=utf-8

from thread import get_ident


class Proxy(object):
    def __init__(self, func, name=None):
        object.__setattr__(self, "__func__", func)
        object.__setattr__(self, "__name__", name)

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
