# coding=utf-8
"""
一个简单的模版引擎
支持以下语法:
    {{# 这是注释 #}}
    {{x}}
    {% if a %}...{% endif %}
    {% for x in list %}...{% endfor %}
"""

import re


class CodeBuilder(object):
    """
    负责生成python代码
    """

    def __init__(self, indent_level=0):
        self.indent_level = indent_level
        self.codes = []

    INDENT_STEP = 4

    def indent(self):
        """
        缩进代码
        """
        self.indent_level += self.INDENT_STEP

    def deindent(self):
        """
        缩退代码
        """
        self.indent_level -= self.INDENT_STEP

    def add_lines(self, line):
        """
        根据缩进加入代码
        """
        self.codes.append(" " * self.indent_level + line)

    def __str__(self):
        return "\n".join(self.codes)

    def get_global(self):
        """
        将render函数发不到global
        :return:
        """
        python_source = str(self)
        global_vars = {}
        exec (python_source, global_vars)
        return global_vars


class Template(object):

    def __init__(self, tpl, *context):
        self.context = {}
        self.text = tpl

        for c in context:
            self.context.update(c)

        self.cb = CodeBuilder()
        self.buffered = []  # 用来保存中间生成的结果

    def flush_buffer(self):
        """
        每次进入以{% 开头就要清空， 或者在解析的最后清空
        """
        if len(self.buffered) == 1:
            self.cb.add_lines("result.append(%s)" % self.buffered[0])
        elif len(self.buffered) > 1:
            self.cb.add_lines("result.extend([%s])" % ",".join(self.buffered))
        self.buffered = []

    def resolve_var(self, expr):
        if expr in self.loop_vars:
            return expr
        if "." in expr:
            expr_splits = expr.split(".")
            return "context['%s'].%s" % (expr_splits[0], expr_splits[1])
        else:
            return "context['%s']" % expr

    def analysis(self):
        self.cb.add_lines("def render_func(context):")
        self.cb.indent()
        self.cb.add_lines("result=[]")  # result用来保存最后生成的结果
        self.cb.add_lines("to_str=str")

        self.op_type = []
        self.loop_vars = []

        # see https://docs.python.org/2/library/re.html#re.S
        tokens = re.split(r"(?s)({{.*?}}|{%.*? %}|{#.*?#})", self.text)
        for token in tokens:
            if token.startswith("{#"):
                continue
            elif token.startswith("{{"):
                expr = token[2:-2].strip()
                self.buffered.append(self.resolve_var(expr))
            elif token.startswith("{%"):
                self.flush_buffer()
                words = token[2:-2].strip().split()
                if words[0] == "if":
                    if len(words) != 2:
                        raise Exception("can not understand if")
                    self.op_type.append("if")
                    self.cb.add_lines("if context[%s]:" % repr(words[1]))
                    self.cb.indent()
                if words[0] == "for":  # "{% for x in list %}"
                    self.op_type.append("for")
                    self.cb.add_lines("for %s in context[%s]:" % (words[1], repr(words[3])))
                    self.loop_vars.append(words[1])
                    self.cb.indent()
                elif words[0].startswith("end"):
                    op_type = words[0][3:]
                    if self.op_type.pop() != op_type:
                        raise Exception("expression error")
                    self.cb.deindent()
            else:
                self.buffered.append(repr(token))
        self.flush_buffer()
        self.cb.add_lines("return ''.join(map(lambda x: str(x), result))")

    def render(self, *args, **kwargs):
        self.context.update(*args)
        self.context.update(kwargs)
        self.analysis()
        global_vars = self.cb.get_global()
        return global_vars['render_func'](self.context)


if __name__ == '__main__':
    tpl = """
    hello {{ name }}
    {# This will be ignored #}
    {% if name %}
        yes
    {% endif %}
    {% for x in list %}
    number: {{x}}
    {% endfor %}
    """
    t = Template(tpl)
    print t.render({"list": [2, 3, 4, 5]}, name="haihui")
