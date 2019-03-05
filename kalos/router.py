# coding=utf-8

import re
from decimal import Decimal

from kalos.verb import Verb


class Router(object):
    """
    路由封装 ,支持`/a/b/<:id|int>` 这种形式
    :param group: 分组，分组可以看成是url的前缀
    :param url: url和group共同构成完整的url
    :methods: 注册的方法 见`httpY.verb.Verb`
    """

    def __init__(self, group="", url="", methods=None):
        self.group = group
        self.url = url
        if not methods:
            methods = [Verb.GET]
        if type(methods) is not list:
            methods = [methods]
        methods.sort()
        self.methods = methods
        self.complete_url = ("/" if self.group else "") + self.group + self.url

    @property
    def has_variable(self):
        return re.search(r"<:.*>", self.complete_url) is not None

    def __repr__(self):
        return "{}-{}".format(self.complete_url, self.methods)

    @property
    def router(self):
        return repr(self)

    def __hash__(self):
        return hash(self.router)

    def __eq__(self, other):
        """
        所谓的相等，是指能否在对方找到匹配条件, 先比较url, 再比较mthod
        """
        if self.has_variable or other.has_variable:
            url_splits = self.complete_url.split("/")
            other_splits = other.complete_url.split("/")
            if len(url_splits) != len(other_splits):
                return False
            for index in xrange(len(url_splits)):
                if re.match(r"<:.*>", url_splits[index]):
                    continue
                else:
                    if url_splits[index] == other_splits[index]:
                        continue
                    else:
                        if re.match(r"<:.*>", other_splits[index]):
                            continue
                        else:
                            return False
            else:
                # url匹配, 再比较method
                if set(self.methods).intersection(set(other.methods)):
                    return True
                else:
                    return False
        # 不存在变量
        if self.router == other.router:
            return True
        if self.complete_url == other.complete_url:
            if set(self.methods).intersection(set(other.methods)):
                return True
            return False

    def get_variable_list(self, url):
        """
        解析变量
        :param url:
        :return:
        """
        result = []
        if not self.has_variable:
            return result
        self_splits = self.complete_url.split("/")
        url_splits = url.split("/")
        for index in xrange(len(self_splits)):
            s = self_splits[index]
            if re.match(r"<:.*>", s):
                # <:id|int>
                s = s[2:-1]
                ss = s.split("|")
                v = url_splits[index]
                if len(ss) > 1:
                    try:
                        if ss[1] == "int":
                            v = int(v)
                        elif ss[1] == "float":
                            v = float(v)
                        elif ss[1] == "decimal":
                            v = Decimal(v)
                    except ValueError as e:
                        raise e
                result.append(v)
        return result
