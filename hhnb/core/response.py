"""
This package provide a useful class to handle HttpResponse in a easy way.
"""


from dis import dis
from genericpath import isfile
from os import stat
from typing import Tuple
from django.http.response import JsonResponse, HttpResponse, FileResponse, HttpResponseNotAllowed
from multipledispatch import dispatch
import json
import os


def _http_response(status_code, content):
    """
    This private function takes the status code, a content
    and returns a simple HttpResponse object.
    """
    return HttpResponse(content, status=status_code)


def _json_response(status_code, data, safe=False):
    """
    This private function takes the status code, some data and 
    return a JsonResponse object. Optionally the safe flag can
    be set True (False by default) to prevent the serialization
    of non "dict" obejcts. 
    """
    return JsonResponse(data=data, status=status_code, safe=safe,
                        content_type='application/json')


def _file_response(file_path):
    """
    This private function takes a file path string and returns 
    a FileResponse object.

    If the file is not found an HttpResponse("File not found", status=404)
    object will be return.
    """
    if os.path.exists(file_path) and os.path.isfile(file_path):
        filename = os.path.split(file_path)[1]
        return FileResponse(open(file_path, 'rb'), as_attachment=True,
                            filename=filename)
    else:
        return _http_response(404, 'File not found')


class ResponseUtil:
    """
    A static class to handle the HttpResponse.
    """

    @staticmethod
    def raw_response(content, *args, **kwargs):
        """
        Returns a raw HttpResponse.

        Parameters
        ----------
        content : any
            the content of the response

        Returns
        -------
        HttpResponse
        """
        return HttpResponse(content, *args, **kwargs)

    @staticmethod
    @dispatch()
    def ok_response():
        """
        Returns a 200 HttpResponse.
        """
        return _http_response(200, b'OK')

    @staticmethod
    @dispatch(str)
    def ok_response(msg):
        """
        Returns a 200 HttpResponse with a custom message.
        """
        return _http_response(200, msg)

    @staticmethod
    @dispatch(int)
    def ko_response(code):
        """
        Returns an error HttpResponse with a custom error code.
        """
        return _http_response(code, b'KO')


    @staticmethod
    @dispatch(int, str)
    def ko_response(code, msg):
        """
        Returns an error HttpResponse with a custom error code and message. 
        """
        return _http_response(code, msg)

    @staticmethod
    @dispatch(str)
    def ko_response(msg):
        """
        Returns a 400 HttpResponse with a custom message. 
        """
        return _http_response(400, msg)

    @staticmethod
    @dispatch()
    def ok_json_response():
        """
        Returns a 200 JsonResponse with an empty json. 
        """
        return _json_response(200, {})

    @staticmethod
    @dispatch(str)
    def ok_json_response(data):
        """
        Returns a 200 JsonResponse with a custom json.
        """
        return _json_response(200, data)

    @staticmethod
    @dispatch(dict)
    def ok_json_response(data):
        """
        Returns a 200 JsonResponse with a custom json.
        """
        return _json_response(200, data)

    @staticmethod
    @dispatch(dict, bool)
    def ok_json_response(data, safe):
        """
        Returns a 200 JsonResponse with a custom json.
        """
        return _json_response(200, data, safe)

    @staticmethod
    @dispatch(str)
    def ko_json_response(data):
        """
        Returns a 400 JsonResponse with a custom json.
        """
        return _json_response(400, data)

    @staticmethod
    @dispatch(dict)
    def ko_json_response(data):
        """
        Returns a 400 JsonResponse with a custom json.
        """
        return _json_response(400, data)

    @staticmethod
    @dispatch(int, str)
    def ko_json_response(code, data):
        """
        Returns an error JsonResponse with a custom erro code and json.
        """
        return _json_response(code, data)

    @staticmethod
    @dispatch(int, dict)
    def ko_json_response(code, data):
        """
        Returns an error JsonResponse with a custom erro code and json.
        """
        return _json_response(code, data)

    @staticmethod
    def file_response(file_path):
        """ 
        Returns a simple FileResponse.
        """
        return _file_response(file_path)

    @staticmethod
    def no_exc_code_response():
        """
        Returns a 404 HttpResponse when the "exc" code is not found.
        """
        return _http_response(404, 'exc code not found')

    @staticmethod
    def method_not_allowed(allowed_methods):
        """
        Returns an error HttpResponse when the request's method is not allowed. 
        """
        return HttpResponseNotAllowed(allowed_methods)