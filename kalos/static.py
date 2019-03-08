# coding=utf-8

import os

import time
from datetime import datetime

from kalos.mime import Suffix_mime
from kalos.response import Response
from kalos.utils import cookie_date, de_cookie_date


class StaticFile(object):
    def __init__(self, app):
        self.app = app
        self.file_cache = dict()

    def __call__(self, request, file_path):
        """
        :param file_path: /test.png
        :return:
        """
        try:
            file_type = file_path.split(".")[-1]
            file_name = file_path.split("/")[-1]
            mime = Suffix_mime[file_type]
            data, stat, code = self.data(request, file_path)
            resp = Response(data=data, content_type=mime, status=code)
            resp.headers.extend([
                ("Content-Disposition", "filename={}".format(file_name)),
                ("Last-Modified", cookie_date(datetime.fromtimestamp(stat.st_mtime)))])
            resp.headers.append(("Content-Length", str(stat.st_size)))
            return resp
        except IOError:
            return Response(status=404)

    def data(self, request, file_path):
        try:
            full_path = self.app.static_path + file_path
            buffered = []
            f = open(full_path, "r")
            stat = os.fstat(f.fileno())
            if_modified_since = request.headers.get("IF-MODIFIED-SINCE")
            if if_modified_since:
                dt = de_cookie_date(if_modified_since)
                if abs(time.mktime(dt.timetuple()) - stat.st_mtime) <= 0.99:
                    return "", stat, 304
            with f:
                while True:
                    data = f.read(1024)
                    if data == "":
                        break
                    else:
                        buffered.append(data)
            return "".join(buffered), stat, 200
        except IOError as e:
            raise e
