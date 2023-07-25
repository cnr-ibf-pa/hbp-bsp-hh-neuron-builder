"""
This package provide a useful class to handle HttpResponse in a easy way.
"""


from django.http.response import JsonResponse, HttpResponse, FileResponse, HttpResponseNotAllowed
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
    of non "dict" objects.
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
    def ok_response(*args):
        """
        Generate an OK response for the given arguments.

        Parameters
        ----------
        *args : variable-length argument list
            Variable length arguments. Accepts 0, 1, or 2 arguments.
            - If no arguments are provided, returns a 200 OK response.
            - If a single integer argument is provided:
                - If the argument is 204, returns a 204 No Content response.
                - Otherwise, returns a response with the provided status code and 'OK' message.
            - If a single string argument is provided, returns a response with a 200 status code and the provided message.
            - If two arguments are provided:
                - If the first argument is an integer and the second argument is a string, returns a response with the provided status code and message.
                - If the first argument is a string and the second argument is an integer, returns a response with the provided status code and message (reversed order).

        Returns
        -------
        HttpResponse
            An HTTP response with the appropriate status code and message.

        Raises
        ------
        TypeError
            If the number or type of arguments is invalid.
        """

        if len(args) == 0:
            return _http_response(200, 'OK')
        elif len(args) == 1:
            if type(args[0]) == int:
                if args[0] == 204:
                    return _http_response(args[0], 'No content')
                else:
                    return _http_response(args[0], 'OK')
            if type(args[0]) == str:
                return _http_response(200, args[0])
        elif len(args) == 2:
            if type(args[0]) == int and \
                type(args[1]) == str:
                return _http_response(args[0], args[1])
            elif type(args[0]) == str and \
                type(args[1]) == int:
                return _http_response(args[1], args[0])
            else:
                raise TypeError('ok_response() takes 1 int and 1 str and 2 int or 2 str was given.')

    @staticmethod
    def ko_response(*args):
        """
        This static method is used to generate a KO response based on the given arguments.

        Parameters
        ----------
        *args : tuple
            Variable length argument list. The arguments can be of different types and lengths.
            The function supports the following argument combinations:
            - No arguments: returns a 400 'KO' response.
            - One integer argument: returns a response with the given status code and a 'KO' message.
            - One string argument: returns a 400 response with the given error message.
            - Two arguments, an integer followed by a string: returns a response with the given status code and error message.
            - Two arguments, a string followed by an integer: returns a response with the given status code and error message.

        Returns
        -------
        response : Response
            A response object with the appropriate status code and message.

        Raises
        ------
        TypeError
            If the argument combinations are not supported.
        """

        if len(args) == 0:
            return _http_response(400, 'KO')
        elif len(args) == 1:
            if type(args[0]) == int:
                if args[0] == 404:
                    return _http_response(args[0], 'Not found')
                else:
                    return _http_response(args[0], 'KO')
            if type(args[0]) == str:
                return _http_response(400, args[0])
        elif len(args) == 2:
            if type(args[0]) == int and \
                type(args[1]) == str:
                return _http_response(args[0], args[1])
            elif type(args[0]) == str and \
                type(args[1]) == int:
                return _http_response(args[1], args[0])
            else:
                raise TypeError('ok_response() takes 1 int and 1 str and 2 int or 2 str was given.')

    @staticmethod
    def ok_json_response(dict={}, safe=False):
        """
        Generate the function comment for the given function body in a markdown code block with the correct language syntax.

        Parameters
        ----------
        dict : dict, optional
            A dictionary containing the response data (default is an empty dictionary).
        safe : bool, optional
            A boolean indicating whether the response data should be sanitized (default is False).

        Returns
        -------
        dict
            The JSON response containing the response data.
        """

        return _json_response(200, dict, safe)

    @staticmethod
    def ko_json_response(dict={}, safe=False):
        """
        A static method that generates a JSON response with a status code of 400.

        Parameters
        ----------
        dict : dict, optional
            A dictionary containing the JSON data to be returned in the response (default: empty dictionary)
        safe : bool, optional
            A boolean indicating whether the JSON data should be safely encoded (default: False)

        Returns
        -------
        dict
            The JSON response with a status code of 400
        """

        return _json_response(400, dict, safe)

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
