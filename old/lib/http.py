"""
HTTP request and response objects. Mainly look into the django code at:
django/http/__init__.py.
"""
from pprint import pformat

class HttpRequest(object):
    """A basic HTTP request. Each HTTP request represents an event that the
    dispatcher/request handler has to work down."""

    def __init__(self):
        self.GET, self.POST, self.COOKIES, self.META, self.FILES = {}, {}, {}, {}, {}
        self.path = ''
        self.path_info = ''
        self.method = None

    def __repr__(self):
        return '<HttpRequest\nGET:%s,\nPOST:%s,\nCOOKIES:%s,\nMETA:%s>' % \
            (pformat(self.GET), pformat(self.POST), pformat(self.COOKIES),
            pformat(self.META))

class HttpResponse(object):
    """A basic HTTP response object. This is the base class. The most common
    use is a 301 redirect response (see HttpResponseRedirect)"""

    status_code = 200

    def __init__(self):
        self._headers = { }

class HttpResponseRedirect(HttpResponse):
    """A http response that redirects to another URL. Returns a 302 status
    code."""

    status_code = 302

    def __init__(self, redirect_to):
        self.location = redirect_to

class HttpResponseNotFound(HttpResponse):
    """A http response in case a request is not found. Should return a 404
    status code.
    """
    status_code = 404

class HttpResponseForbidden(HttpResponse):
    """A http response if the request is forbidden. Returns a 403 status
    code."""
    status_code = 403
