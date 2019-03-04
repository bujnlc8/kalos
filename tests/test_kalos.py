# coding=utf-8

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kalos.server import Kalos
from kalos.response import Response
import json
from kalos.local import request

books = dict()


class Book(object):
    def __init__(self, id_, name):
        self.id_ = id_
        self.name = name

    def to_string(self):
        return json.dumps({
            "id_": self.id_,
            "name": self.name})


if __name__ == "__main__":
    app = Kalos()

    @app.route(group="book", url="/put", methods=["POST"])
    def add_book():
        print request, request.form
        id_ = request.form.get("id", m=int)
        name = request.form.get("name")
        book = Book(id_=id_, name=name)
        books.update({
            id_: book
        })
        return book.to_string(), 200

    @app.route(group="book", url="/<:id|int>", methods="GET")
    def get_book(id):
        book = books.get(id)
        if not book:
            return "", 404
        return book.to_string()

    @app.route(group="book", url="/<:id|int>", methods=["DELETE"])
    def delete_book(id):
        books.pop(id)
        return json.dumps({"code": 0, "len": len(books)})

    @app.route(url="/redirect")
    def redirect():
        r = Response(status=302, Location="https://www.google.com")
        return r

    app.run()