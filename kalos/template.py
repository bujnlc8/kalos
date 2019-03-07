# coding=utf-8
"""
一个简单的模版引擎
支持以下语法:
    {{# 这是注释 #}}
    {{x}}
    {% if a %}...{% endif %}
    {% for x in list %}...{% endfor %}
    {py
        print a+b
    py}
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
        self.indent_level += self.INDENT_STEP

    def deindent(self):
        self.indent_level -= self.INDENT_STEP

    def add_lines(self, line):
        self.codes.append(" " * self.indent_level + line)

    def __str__(self):
        return "\n".join(self.codes)

    def get_global(self):
        """
        将render函数发布到global
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

    @staticmethod
    def resolve_var(expr):
        split_tokens = re.split(r"(?s)(\.|\|)", expr.replace(" ", ""))
        index = 0
        result = split_tokens[index]
        index += 1
        while index < len(split_tokens):
            try:
                # 找操作符
                operator = split_tokens[index]
                if operator not in (".", "|"):
                    raise Exception('do not support operator %s' % operator)
            except IndexError:
                index += 1
            except Exception as e:
                raise
            else:
                # 找操作数
                index += 1
                try:
                    operand = split_tokens[index]
                except Exception as e:
                    raise e
                else:
                    if operand:
                        if operator == ".":
                            result = "getattr(%s, %s)" % (result, repr(operand))
                        elif operator == "|":
                            result = result + ".%s()" % operand
                    index += 1
        return result

    def analysis(self):
        self.cb.add_lines("def render_func(context):")
        self.cb.indent()
        self.cb.add_lines("result=[]")  # result用来保存最后生成的结果
        self.cb.add_lines("to_str=str")
        # 将context中的变量释放为单个变量
        for key in self.context.keys():
            self.cb.add_lines("%s = context['%s']" % (key, key))

        self.op_type = []

        # see https://docs.python.org/2/library/re.html#re.S
        tokens = re.split(r"(?s)({{.*?}}|{%.*? %}|{#.*?#}|{py.*?py})", self.text)
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
                    self.cb.add_lines("if %s :" % words[1])
                    self.cb.indent()
                if words[0] == "for":  # "{% for x in list %}"
                    self.op_type.append("for")
                    self.cb.add_lines("for %s in %s:" % (words[1], words[3]))
                    self.cb.indent()
                elif words[0].startswith("end"):
                    op_type = words[0][3:]
                    if self.op_type.pop() != op_type:
                        raise Exception("expression error")
                    self.cb.deindent()
            elif token.startswith("{py"):
                py = token[3:-3]
                segments = py.split("\n")
                start_blank = 0
                for segment in segments:
                    if len(segment) == 0:
                        continue
                    else:
                        for x in segment:
                            if x in ("\t", " "):
                                start_blank += 1
                            else:
                                break
                        break
                for segment in segments:
                    # 去除前面的start_bank个空格
                    segment = segment[start_blank:]
                    if segment.replace(" ", "").replace("\t", "").startswith("print"):
                        blank_num = 0
                        for x in segment:
                            if x in (" ", "\t"):
                                blank_num += 1
                            else:
                                break
                        self.flush_buffer()
                        self.cb.add_lines("%sresult.append(%s)" % (
                            segment[:blank_num], segment[blank_num + 5:]))
                    else:
                        self.cb.add_lines(segment)
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
    {{a.b.b | upper}} {{a.b.b }}
    {# This will be ignored #}
    {% if name %}
        yes
    {% endif %}
    {% for x in list %}
    number: {{x}}
    {% endfor %}
    {py
    print 200+b
    for x in xrange(b):
        print(str(x) + '\\n')
    py}
    """

    class B(object):
        b = 'aBc'

    class A(object):
        b = B()
    a = A()
    t = Template(tpl)
    print t.render({"list": [2, 3, 4, 5]}, name="haihui", a=a, b=100)
