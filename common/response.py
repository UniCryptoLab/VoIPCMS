#!/usr/bin/python
# -*- coding: utf-8 -*-

from django.http import HttpResponse
import json
import hashlib

class Response(object):
    def __init__(self, code, msg, data):
        self._code = code
        self._msg = msg
        self._data = data

    def to_dict(self):
        dict = {}
        dict['code']= self._code
        dict['msg'] = self._msg
        dict['data'] = self._data

        return dict


class Error(Response):
    def __init__(self, msg, code=1):
        super(Error, self).__init__(code, msg, None)


class Success(Response):
    def __init__(self, data=None, msg='success',):
        super(Success, self).__init__('OK', msg, data)


def json_response(obj):
    return HttpResponse(_json_content(obj), content_type="application/json", charset='utf-8')


def _json_content(obj):
    if issubclass(obj.__class__, Response):
        return json.dumps(obj.to_dict(), ensure_ascii=False)
    return json.dumps(obj, ensure_ascii=False, indent=4)


def _calc_md5(content):
    m = hashlib.md5()
    m.update(content.encode('utf-8'))
    md5 = m.hexdigest()
    return md5

def _json_content_md5(obj):
    content = _json_content(obj)
    return  _calc_md5(content)
