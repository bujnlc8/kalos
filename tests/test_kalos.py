# coding=utf-8

import os

import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from kalos.server import Kalos
from kalos.response import Response
from kalos.request import request
from kalos.session import session, login_required

books = dict()


class Book(object):
    def __init__(self, id_, name):
        self.id_ = id_
        self.name = name

    def to_string(self):
        return json.dumps({
            "id_": self.id_,
            "name": self.name})


def p(*args):
    print(args)


app = Kalos()

if __name__ == "__main__":
    @app.register_app_error_handler(401)
    def handle():
        return json.dumps({
            "code": 401,
            "msg": "未授权"
        }), 401
    app.register_before_handle(lambda :  p("before handle"))
    app.register_after_handle(lambda :  p("after handle"))
    app.register_before_request(lambda : p("before request"))
    app.register_after_request(lambda x: x)

    # it works as add_book = app.route(...)(login_required(add_book))
    @app.route(group="book", url="/put", methods=["PUT"])
    @login_required
    def add_book():
        id_ = request.form.get("id", m=int)
        name = request.form.get("name")
        book = Book(id_=id_, name=name)
        books.update({
            id_: book
        })
        return book.to_string(), 200

    @app.route(group="book", url="/put", methods=["POST"])
    def add_book():
        id_ = request.form.get("id", m=int)
        name = request.form.get("name")
        book = Book(id_=id_, name=name)
        books.update({
            id_: book
        })
        return book.to_string(), 200

    @app.route(group="book", url="/<:id|int>", methods="GET")
    def get_book(id):
        print id, 00000
        book = books.get(id)
        if not book:
            return "", 404
        return book.to_string()

    @app.route(group="book", url="/<:id|int>", methods=["DELETE"])
    def delete_book(id):
        try:
            books.pop(id)
        except KeyError:
            pass
        return json.dumps({"code": 0, "len": len(books)})

    @app.route(url="/redirect")
    def redirect():
        r = Response(status=302, Location="https://www.google.com")
        return r

    app.run()