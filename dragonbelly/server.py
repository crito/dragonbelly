#!/usr/bin/env python
#
# Copyright 2009 Christo Buschek
#
#
"""A asynchronous HTTP server."""

import logging
import time
import socket
#import urlparse
import errno
import select

DEFAULT_ERROR_MESSAGE = """\
<html><head>
<title>Dragonbelly error response</title>
</head>
<body>
<h1>Error response</h1>
<p>Errorcode %(code)d.
<p>Message: %(message)s.
<p>Error code explanation: %(code)s = %(explain)s.
</body></html>
"""

class IOLoop(object):
    def __init__(self, poll):
        self._poll = poll

class HTTPServer(object):
    def __init__(self, host, port, request_handler=None):
        self.host = host
        self.port = port
        self.request_handler = request_handler
        self._socket = None

    def run(self, poll_interval=None):
        # http://scotdoyle.com/python-epoll-howto.html
        EOL1 = b'\n\n'
        EOL2 = b'\n\r\n'
        response  = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
        response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
        response += b'Hello, world!'

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.listen(1)
        self._socket.setblocking(0)
        
        self._epoll = select.epoll()
        self._epoll.register(self.fileno(), select.EPOLLIN)

        self._serving = True
        try:
            c = {}; r = {}; w = {}
            while self._serving:
                #r, w, e = select.select([self], [], [], poll_interval)
                #if r:
                #    self._handle_request()
                #c, a = self.get_request()
                events = self._epoll.poll(1)
                for fileno, event in events:
                    if fileno == self._socket.fileno():
                        connection, address = self._socket.accept()
                        connection.setblocking(0)
                        self._epoll.register(connection.fileno(), select.EPOLLIN)
                        c[connection.fileno()] =  connection
                        r[connection.fileno()] = b''
                        w[connection.fileno()] = response

                    elif event & select.EPOLLIN:
                        r[fileno] +=  c[fileno].recv(1024)
                        if EOL1 in r[fileno] or EOL2 in r[fileno]:
                            self._epoll.modify(fileno, select.EPOLLOUT)
                            #print('-'*40 + '\n' + r[fileno].decode()[:-2])
                    elif event & select.EPOLLOUT:
                        byteswritten = c[fileno].send(w[fileno])
                        w[fileno] = w[fileno][byteswritten:]
                        if len(w[fileno]) == 0:
                            self._epoll.modify(fileno, 0)
                            c[fileno].shutdown(socket.SHUT_RDWR)
                    elif event & select.EPOLLHUP:
                        self._epoll.unregister(fileno)
                        c[fileno].close()
                        del c[fileno]
        except Exception as e:
            print(e)
        finally:
            self.shutdown()

    def shutdown(self):
        self._epoll.unregister(self._socket.fileno())
        self._epoll.close()
        self._socket.close()

#                try:
#                    c, a = self._socket..accept()
#                except socket.error, e:
#                    if e[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
#                        return
#                    raise
#
#                self._handle_request(c, a)
#            self.shutdown()

        self._socket.close()

    def _handle_request(self, connection, address):
        #print "%s from %s" % (time.time(), address)
        #while True:
        data = connection.recv(1024)
        #    if data == 'done': break
        #print data
        connection.send(data)
        connection.close()

    def fileno(self):
        """Return socket file number."""
        return  self._socket.fileno()

    def get_request(self):
        """Get the request."""
        return self._socket.accept()

class HTTPRequestHandler(object):
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server

    def parse_request(self):
        """Parse a request."""

class HTTPResponse(object):
    pass

if __name__ == "__main__":
    h = HTTPServer('', 6565)
    h.run()
