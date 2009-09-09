"""
brokerd - Manage incoming HTTP requests and redirect these requests
          after passing a load balancer function to a webserver with
          the physical URL available.
"""

import logging
import logging.handlers
import queue
from http.server import HTTPServer, BaseHTTPRequestHandler

__version__  = '0.1'
__progname__ = 'brokerd'

logfile = '/var/log/brokerd.log'
log = logging.getlogger('brokerd')
log.setLevel(logging.DEBUG)
log_handler = logging.handlers.FileHandler(logfile)
log.addHandler(log_handler)

class Event(object):
    def __init__(self):
        self.request = ''

    def add(self, request):
        self.request = request

    def get(self):
        return self.request

class EventQueue(object):
    def __init__(self):
        self.queue = queue.Queue(1024)

    def put(self, item):
        self.queue.put_nowait(item)

    def get(self):
        item = self.queue.get()
        return item

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        e = Event()
        e.add
