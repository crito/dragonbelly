"""
brokerd - Manage incoming HTTP requests and redirect these requests
          after passing a load balancer function to a webserver with
          the physical URL available.
"""

import sys
import logging
import logging.handlers
import queue, heapq, time
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
        log.debug('Event key/value added: %s => %s' % (key, value))
        self.data[key] = value

    def get(self):
        log.debug('Event key/value retrieved: %s => %s' % (key, value))
        return self.request

    def add_to_queue():
        pass

class EventQueue(queue.Queue):
    """
    FIFO Queue qith Priority handling.
    See Python Cookbook, chapter 9, recipe 3 (Priority Queue).
    """
    def _init(self, maxsize):
        """Initializes the array to use for the eventQueue. Called by 
        __init__() of the parent class."""
        self.maxsize = maxsize
        self.queue = [ ]

    def _qsize(self):
        """Return current amount of elements of the EventQueue."""
        return len(self.queue)

    def _empty(self):
        """Check whether the EventQueue is empty."""
        return not self.queue

    def _full(self):
        """Check whether EventQueue is full."""
        return self.maxsize > 0 and len(self.queue) >= self.maxsize

    def _put(self, item):
        """Put a new item onto the queue."""
        heapq.heappush(self.queue, item)

    def _get(self):
        """Retrieve next item from the queue."""
        return heapq.heappop(self.queue)

    def put(self, item, priority=0, block=True, timeout=None):
        """Override Queue.Queue's put function to incorporate the priority
        argument."""
        decorated_item = priority, time.time(), item
        queue.Queue.put(self, decorated_item, block, timeout)

    def get(self, block=True, timeout=None):
        """Override Queue.Queue's get function."""
        priority, time_posted, item = queue.Queue.get(self, block, timeout)
        return item

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        e = Event()
        e.add('method', 'GET')
        e.add('path', self.path)
        e.add('http_version', self.request_version)
        q.put(e)
        log.debug("Queue Size: %d" % q.qsize())
        log.debug("Adding event")

    def do_PUT(self):
        pass

class HttpListener(object):
    def __init__(self, host, port):
        self.server_address = (host, port)
        self.httpd = HTTPServer(self.server_address, RequestHandler)

    def run(self):
        self.httpd.serve_forever()

class Dispatcher(object):
    def __init__(self):
        self.event_handlers = []

if __name__ == "__main__":
    q = EventQueue()
    h = HttpListener('localhost', 8000)
    h.run()
