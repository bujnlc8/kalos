# coding=utf-8

from kalos.server import Kalos

views = [
    "demo.view",
    "demo.middleware"
]


def create_app():
    app = Kalos(app_file=__file__)
    for view in views:
        app.register_roselle(view)
    return app
