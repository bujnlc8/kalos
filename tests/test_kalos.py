# coding=utf-8

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kalos.server import Kalos
from kalos.response import Response, make_redirect

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

    @app.route(url="/redirect")
    def redirect(request):
        r = Response(status=302, Location="https://www.google.com")
        return r

    @app.route(url="/redirect1")
    def redirect(request):
        r = make_redirect(location="https://www.google.com")
        return r, 301

    app.run()
