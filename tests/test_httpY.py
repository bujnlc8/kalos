# coding=utf-8

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from httpY.server import HttpY

if __name__ == "__main__":
    app = HttpY()

    @app.route(group="book", url="/<:id>")
    def book(*args):
        return "book"

    @app.route(group="", url="/abc", methods=["POST"])
    def test2(*args):
        return "test2"

    @app.route(group="", url="/abc", methods=["get"])
    def test3(*args):
        return "test3"

    app.run()
