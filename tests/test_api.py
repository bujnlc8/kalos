# coding=utf-8

from __future__ import unicode_literals

import json
import os
import unittest

import requests

api_list = {
    "put_put": "http://127.0.0.1:10101/book/put",
    "put": "http://127.0.0.1:10101/book/put",
    "get": "http://127.0.0.1:10101/book/1",
    "delete": "http://127.0.0.1:10101/book/1",
    "redirect": "http://127.0.0.1:10101/redirect"
}


class TestApi(unittest.TestCase):
    def tearDown(self):
        os.system("ps -ef | grep 'python -m tests.test_kalos'  | grep -v 'grep' | awk '{print $2}' | xargs kill -9")

    def test_api(self):
        response = requests.request("PUT", url=api_list["put_put"], data={"id": 1, "name": "十万个为什么"})
        assert response.status_code == 401
        print response.text, '****'

        response = requests.request("POST", url=api_list["put"], data={"id": 1, "name": "十万个为什么"})
        assert response.status_code == 200
        assert json.loads(response.text)["id_"] == 1

        response = requests.request("GET", url=api_list["get"])
        assert response.status_code == 200
        assert json.loads(response.text)["id_"] == 1
        assert json.loads(response.text)["name"] == "十万个为什么"

        response = requests.request("DELETE", url=api_list["delete"])
        assert response.status_code == 200
        assert json.loads(response.text)["len"] == 0

        response = requests.request("GET", url=api_list["get"])
        assert response.status_code == 404

        response = requests.request("GET", url=api_list["redirect"], allow_redirects=False)
        assert response.status_code == 302


if __name__ == "__main__":
    unittest.main()
