"""
brokerd - Manage incoming HTTP requests and redirect these requests
          after passing a load balancer function to a webserver with
          the physical URL available.
"""

import sys
import os
import logging
import logging.handlers
import queue, heapq, time
from threading import Timer
from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser
import signal

__version__  = '0.2'
__progname__ = 'brokerd'

class DragonbellyError(Exception): pass
class ConfigError(DragonbellyError): pass

logfile = '/var/log/brokerd.log'
log = logging.getLogger('brokerd')
log.setLevel(logging.DEBUG)
log_handler = logging.FileHandler(logfile)
log.addHandler(log_handler)

class Event(object):
    """An Event is a single incoming request. A request is a HTTP command and is
    stored as an event in a queue."""
    def __init__(self):
        self._data = {}

    def add(self, key, value):
        log.debug('Event key/value added: %s => %s' % (key, value))
        self._data[key] = value

    def get(self, key):
        log.debug('Event key retrieved: %s' % key)
        return self._data[key]

class EventQueue(queue.Queue):
    """
    FIFO Queue qith Priority handling.
    See Python Cookbook, chapter 9, recipe 3 (Priority Queue).
    """
    def _init(self, maxsize):
        """Initializes the array to use for the eventQueue. Called by 
        __init__() of the parent class."""
        self._maxsize = maxsize
        self._queue = [ ]

    def _qsize(self):
        """Return current amount of elements of the EventQueue."""
        return len(self._queue)

    def _empty(self):
        """Check whether the EventQueue is empty."""
        return not self._queue

    def _full(self):
        """Check whether EventQueue is full."""
        return self._maxsize > 0 and len(self._queue) >= self._maxsize

    def _put(self, item):
        """Put a new item onto the queue."""
        heapq.heappush(self._queue, item)

    def _get(self):
        """Retrieve next item from the queue."""
        return heapq.heappop(self._queue)

    def put(self, item, priority=0, block=False, timeout=None):
        """Override Queue.Queue's put function to incorporate the priority
        argument."""
        decorated_item = priority, time.time(), item
        queue.Queue.put(self, decorated_item, block, timeout)

    def get(self, block=False, timeout=None):
        """Override Queue.Queue's get function."""
        priority, time_posted, item = queue.Queue.get(self, block, timeout)
        return item

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        e = Event()
        e.add('method', 'GET')
        e.add('path', self.path)
        e.add('http_version', self.request_version)
        try:
            q.put(e)
            log.debug("Queue Size: %d" % q.qsize())
            log.debug("Adding event")
        except queue.Full as e:
            log.debug("Queue is full. no event added.")
            log.debug(e)

    def do_PUT(self):
        try:
            e = q.get()
            log.debug('Retrieved an event:')
            log.debug('Path: %s' % e.get('path'))
            log.debug('Queue size: %s' % q.qsize())
        except queue.Empty as e:
            log.debug('Queue is empty.')
            log.debug(e)

class HttpListener(object):
    def __init__(self, host, port):
        self._server_address = (host, port)
        self.httpd = HTTPServer(self._server_address, RequestHandler)

    def run(self):
        self.httpd.serve_forever()

class Dispatcher(object):
    def __init__(self):
        self.event_handlers = []

class DragonDomain(object):
    """
    A domain within the dragonbelly context.

    A domain is to dragonbelly what a virtual host is to a webserver.
    """
    def __init__(self):
        pass

class DragonUpstream(object):
    """
    Upstream is a base object for a backend. 

    This object is used for DB backends as well as for a file delivery or file
    upload backend.
    """
    def __init__(self):
        pass

class DragonConfig(object):
    """
    Read and parse the configuration file and the command line arguments.

    There is an order in which configuration options are read:
        1) Default values
        2) Command line options
        3) Configuration file (/etc/dragonbelly/dragonbelly.conf)

    The configuration file obeys a structure similar to the nginx configuration
    file format. See the dragonbelly.conf in the source tree for an example.
    """
    def __init__(self, options):
        self._conf['daemonize'] = options.daemonize
        self._conf['host'] = options.host
        self._conf['port'] = options.port
        self._conf['logfile'] = options.logfile
        self._conf['loglevel'] = options.loglevel
        self._conf['conffile'] = options.conffile

        self._upstreams = {}
        self._domains = {}

        # Load config file and parse its contents
        self.load('/usr/local/etc/dragonbelly.conf')

    def load(self, file):
        """
        Load a configuration file.
        """
        # Load config file ``file``
        try:
            f = open(file, 'r')
            conf = f.readlines()
        except IOError as e:
            raise ConfigError("Error %s while opening config file. %s." % tuple(e.args))
        finally:
            f.close()

        # context and depth for current configuration parsing
        parse_depth = 0
        parse_context = 'global'  

        for row in conf:
            # Remove leading and trailing whitespace
            row = row.strip()
            # Ignore comments and empty lines
            if row[0] == '#' or row[0] == '\0':
                continue

            argv = row.split()
            if argv[0] in 'daemonize' and len(argv) == 2:
                self._conf['daemonize'] = argv[1]
            elif argv[0] in 'listen' and len(argv) == 2:
                listen = argv[1].split(':')
                self._conf['host'] = listen[0]
                if len(listen) == 2:
                    self._conf['port'] = listen[1]
            elif argv[0] in 'logfile' and len(argv) == 2:
                self._conf['logfile'] = argv[1]
            elif argv[0] in 'loglevel' and len(argv) == 2:
                self._conf['loglevel'] = argv[1]

            if argv[0] == 'upstream':
                self._upstreams[argv[1]] = DragonUpstream()
            if argv[0] == 'domain':
                self._domains[argv[1]] = DragonDomain()

            
q = EventQueue()

def main(host, port):
    h = HttpListener(host, port)
    h.run()

def daemonize():
    """
    Daemonize the server.
    """
    # Do the double fork magic
    try:
        pid = os.fork()
        if pid > 0:
            # Exit the parent
            sys.exit(0)
    except OSError as e:
        #log.debug("ddFork failed.")
        #log.debug(e)
        sys.exit(1)

    # decouple from the parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # second fork
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        #log.debug("Second Fork failed.")
        #log.debug(e)
        sys.exit(1)

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-d", "--daemon", action="store_true", dest="daemonize", 
                      default=False, help="Daemonize the brokerd process.")
    parser.add_option("-H", "--host", dest="host", default="127.0.0.1", 
                      help="IP to listen to.")
    parser.add_option("-p", "--port", type="int", dest="port", default=6565, 
                      help="Port to listen to..")
    parser.add_option("-l", "--logfile", dest="logfile", 
                      default="/var/log/dragonbelly.log",  help="File to log to.")
    parser.add_option("-V", "--loglevel", dest="loglevel", 
                      default="DEBUG",  help="Loglevel to log.")
    parser.add_option("-c", "--config", dest="conffile", 
                      default="/etc/dragonbelly/dragonbelly.conf",  help="Config file to use.")

    (options, args) = parser.parse_args()

    if options.daemonize:
        daemonize()
        main(options.host, options.port)
    else:
        try:
            main(options.host, options.port)
        except KeyboardInterrupt:
            print("CTRL-C. Cleaning up.")
            sys.exit(0)
