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
log = logging.getLogger('brokerd')
log.setLevel(logging.DEBUG)
log_handler = logging.FileHandler(logfile)
log.addHandler(log_handler)


class Event(object):
    def __init__(self):
        self.data = {}

    def add(self, key, value):
        log.debug('Event added: %s => %s' % (key, value))
        self.data[key] = value

    def get(self):
        log.debug('Event retrieved: %s => %s' % (key, value))
        return self.request

class EventQueue(object):
    def __init__(self):
        self.queue = queue.Queue(1024)

    def put(self, item):
        self.queue.put_nowait(item)

    def get(self):
        item = self.queue.get()
        return item

    def size(self):
        return self.queue.qsize()

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        e = Event()
        e.add('method', 'GET')
        e.add('path', self.path)
        e.add('http_version', self.request_version)
        q.put(e)
        q.size()

    def do_PUT(self):
        e = Event()
        e.add('method', 'GET')
        e.add('path', self.path)
        e.add('http_version', self.request_version)
        q.put(e)
        q.size()

class HttpListener(object):
    def __init__(self, host, port):
        self.server_address = (host, port)
        self.httpd = HTTPServer(self.server_address, RequestHandler)

    def run(self):
        self.httpd.serve_forever()

class Dispatcher(object):
    def __init__(self):
        self.event_handlers = []


q = EventQueue()
if __name__ == "__main__":
    print("Queue Size: %d" % q.size())
    h = HttpListener('localhost', 8000)
    h.run()

