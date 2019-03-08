# coding=utf-8

from datetime import datetime

from demo.model import Book
from kalos.registry import Roselle
from kalos.response import render_template

ros = Roselle(__file__)


@ros.route(group="book", url="/<id|int>", methods="GET")
def get_book(id):
    return "", 401


@ros.route(url="/")
def index():
    return "ok"


@ros.route(url="/tpl")
def test_tpl():
    tpl = """
        <html>
        <head>
        <title>测试模版引擎</title>
        </head>
        <body>
        hello <b>{{ name }} </b><br>
        now is 
        {py
        print now + '<br/>'
        py}
        book_list:
        <table>
        <tr>
        <th>title</th>
        <th>author</th>
        <th>price</th>
        </tr>
        {% for book in books %}
            <tr>
            <td>{{book.title}} </td>
            <td>{{book.author}}</td>
            <td>{{book.price }}</td>
            </tr>
        {% endfor %}
        </table>
        </body>
        </html>
        """
    books = [Book("解忧杂货店", "东野圭吾", "39.50元")]
    books.append(
        Book("围城", "钱钟书", "19.00元")
    )
    books.append(
        Book("三体", "刘慈欣", "23.00元")
    )
    return render_template(tpl, {
        "name": "linghaihui",
        "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    books=books, )


@ros.route("/tpltpl")
def tpltpl():
    return render_template("test.tpl", name="haihui")


@ros.route("/tplhtml")
def tplhtml():
    return render_template("test.html", name="haihui")