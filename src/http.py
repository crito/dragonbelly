# This file is part of dragonbelly.
#
# Copyright (C) 2010 Christo Buschek <crito@cryptodrunks.net>
#
#   Dragonbelly is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Dragonbelly is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with Dragonbelly. If not, see <http://www.gnu.org/licenses/>.
#
"""
http.py - HTTP related objects.
"""

import sys, os
import logging
import signal
import socket
import time
import urlparse
from dragonbelly import eventloop

class HttpServer(object):
    """
    A single threaded, non-blocking HTTP server.
    """
    def __init__(self, event_handler, event_loop=None):
        self.event_handler = event_handler
        self.event_loop = event_loop or eventloop.EventLoop.instance()
        self._socket = None

    def start(self, addr='127.0.0.1', port=80):
        """Create the socket."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self._socket.bind((addr, port))
        self._socket.listen(128)

    def stop(self):
        """Close the socket."""
        self._socket.close()

    def daemonize(self):
        """Fork the process."""
        # Do the double fork magic
        try:
            pid = os.fork()
            if pid > 0:
                # Exit the parent
                sys.exit(0)
        except OSError, e:
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
        except OSError, e:
            sys.exit(1)

    def handle_event(self, fd, events):
        while True:
            try:
                connection, address = self._socket.accept()
            except socket.error, e:
                # Operation would block, Try again
                if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return
                raise

class HttpParser(object):
    pass
