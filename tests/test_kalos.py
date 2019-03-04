# coding=utf-8

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kalos.server import Kalos

if __name__ == "__main__":
    app = Kalos()

    @app.route(group="book", url="/<:id>")
    def book(request, id):
        print request.args, request.args.get("c", m=str)
        return "book"

    @app.route(group="", url="/abc", methods=["POST"])
    def test2(*args):
        return "test2"

    @app.route(group="", url="/abc", methods=["get"])
    def test3(*args):
        return "test3"

    app.run()
