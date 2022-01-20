from dis import dis
from genericpath import isfile
from os import stat
from typing import Tuple
from django.http.response import JsonResponse, HttpResponse, FileResponse, HttpResponseNotAllowed
from multipledispatch import dispatch
import json
import os


def _http_response(status_code, content):
    return HttpResponse(content, status=status_code)


def _json_response(status_code, data, safe=False):
    return JsonResponse(data=data, status=status_code, safe=safe,
                        content_type='application/json')


def _file_response(file_path):
    if os.path.exists(file_path) and os.path.isfile(file_path):
        filename = os.path.split(file_path)[1]
        return FileResponse(open(file_path, 'rb'), as_attachment=True,
                            filename=filename)
    else:
        return _http_response(404, 'File not found')


class ResponseUtil:

    @staticmethod
    def raw_response(content, *args, **kwargs):
        return HttpResponse(content, *args, **kwargs)

    @staticmethod
    @dispatch()
    def ok_response():
        return _http_response(200, b'OK')

    @staticmethod
    @dispatch(str)
    def ok_response(msg):
        return _http_response(200, msg)

    @staticmethod
    @dispatch(int)
    def ko_response(code):
        return _http_response(code, b'KO')


    @staticmethod
    @dispatch(int, str)
    def ko_response(code, msg):
        return _http_response(code, msg)

    @staticmethod
    @dispatch(str)
    def ko_response(msg):
        return _http_response(400, msg)

    @staticmethod
    @dispatch()
    def ok_json_response():
        return _json_response(200, {})

    @staticmethod
    @dispatch(str)
    def ok_json_response(data):
        return _json_response(200, data)

    @staticmethod
    @dispatch(dict)
    def ok_json_response(data):
        return _json_response(200, data)

    @staticmethod
    @dispatch(dict, bool)
    def ok_json_response(data, safe):
        return _json_response(200, data, safe)

    @staticmethod
    @dispatch(str)
    def ko_json_response(data):
        return _json_response(400, data)

    @staticmethod
    @dispatch(dict)
    def ko_json_response(data):
        return _json_response(400, data)

    @staticmethod
    @dispatch(int, str)
    def ko_json_response(code, data):
        return _json_response(code, data)

    @staticmethod
    @dispatch(int, dict)
    def ko_json_response(code, data):
        return _json_response(code, data)

    @staticmethod
    def file_response(file_path):
        return _file_response(file_path)

    @staticmethod
    def no_exc_code_response():
        return _http_response(404, 'exc code not found')

    @staticmethod
    def method_not_allowed(allowed_methods):
        return HttpResponseNotAllowed(allowed_methods)