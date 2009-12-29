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
    # HTTPServer Class. 
    # Command parsing generously copied from /usr/lib/python3/http/server.py. 
    # keep-alive taken from same source

    error_message_format = DEFAULT_ERROR_MESSAGE
    #self.error_content_type = DEFAULT_ERROR_CONTENT_TYPE
    
    def __init__(self, host, port, request_handler=None):
        self.host = host
        self.port = port
        self.request_handler = request_handler
        self._socket = None

    def run(self, poll_interval=None):
        # http://scotdoyle.com/python-epoll-howto.html
        EOL1 = b'\n\n'
        EOL2 = b'\n\r\n'
        #response  = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
        #response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
        #response += b'Hello, world!'

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self.host, self.port))
        self._socket.listen(256)
        self._socket.setblocking(0)
        
        self._epoll = select.epoll()
        self._epoll.register(self.fileno(), select.EPOLLIN)

        self._serving = True
        try:
            self.c = {}; self.r = {}; self.w = {}
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
                        self.c[connection.fileno()] =  connection
                        self.r[connection.fileno()] = b''
                        self.w[connection.fileno()] = self._handle_request(connection, address)

                    elif event & select.EPOLLIN:
                        self.r[fileno] +=  self.c[fileno].recv(1024)
                        if EOL1 in self.r[fileno] or EOL2 in self.r[fileno]:
                            self._epoll.modify(fileno, select.EPOLLOUT)
                            #print('-'*40 + '\n' + r[fileno].decode()[:-2])
                    elif event & select.EPOLLOUT:
                        byteswritten = self.c[fileno].send(self.w[fileno])
                        self.w[fileno] = self.w[fileno][byteswritten:]
                        if len(self.w[fileno]) == 0:
                            self._epoll.modify(fileno, 0)
                            self.c[fileno].shutdown(socket.SHUT_RDWR)
                    elif event & select.EPOLLHUP:
                        self._epoll.unregister(fileno)
                        self.c[fileno].close()
                        del self.c[fileno]
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
        self.close_connection = 1
        self._handle_one_request()
        while not self.close_connetion:
            self.handle_one_request()

    def _handle_one_request(self):
        self.raw_requestline = self.r.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        mname = 'do_' + self.command
        if not hasattr(self.mname):
            #self.send_error(501, "Unsupported method (%r)" % self.command
            pass
        method = getattr(self, mname)
        method()

        data = connection.recv(1024)
        #    if data == 'done': break
        #print data
        connection.send(data)
        connection.close()

 
    def parse_request(self):
        """Parse a request (internal).

        The request should be stored in self.raw_requestline; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return True for success, False for failure; on failure, an
        error is sent back.

        """
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = 1
        requestline = str(self.raw_requestline, 'iso-8859-1')
        if requestline[-2:] == '\r\n':
            requestline = requestline[:-2]
        elif requestline[-1:] == '\n':
            requestline = requestline[:-1]
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            [command, path, version] = words
            if version[:5] != 'HTTP/':
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            try:
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                # RFC 2145 section 3.1 says there can be only one "." and
                #   - major and minor numbers MUST be treated as
                #      separate integers;
                #   - HTTP/2.4 is a lower version than HTTP/2.13, which in
                #      turn is lower than HTTP/12.3;
                #   - Leading zeros MUST be ignored by recipients.
                if len(version_number) != 2:
                    raise ValueError
                version_number = int(version_number[0]), int(version_number[1])
            except (ValueError, IndexError):
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
                self.close_connection = 0
            if version_number >= (2, 0):
                self.send_error(505,
                          "Invalid HTTP Version (%s)" % base_version_number)
                return False
        elif len(words) == 2:
            [command, path] = words
            self.close_connection = 1
            if command != 'GET':
                self.send_error(400,
                                "Bad HTTP/0.9 request type (%r)" % command)
                return False
        elif not words:
            return False
        else:
            self.send_error(400, "Bad request syntax (%r)" % requestline)
            return False
        self.command, self.path, self.request_version = command, path, version

        # Examine the headers and look for a Connection directive.

        # MessageClass wants to see strings rather than bytes.
        # But a TextIOWrapper around self.r would buffer too many bytes
        # from the stream, bytes which we later need to read as bytes.
        # So we read the correct bytes here, as bytes, then use StringIO
        # to make them look like strings for MessageClass to parse.
        headers = []
        while True:
            line = self.r.readline()
            headers.append(line)
            if line in (b'\r\n', b'\n', b''):
                break
        hfile = io.StringIO(b''.join(headers).decode('iso-8859-1'))
        self.headers = email.parser.Parser(_class=self.MessageClass).parse(hfile)

        conntype = self.headers.get('Connection', "")
        if conntype.lower() == 'close':
            self.close_connection = 1
        elif (conntype.lower() == 'keep-alive' and
              self.protocol_version >= "HTTP/1.1"):
            self.close_connection = 0
        return True
    def fileno(self):
        """Return socket file number."""
        return  self._socket.fileno()

    def get_request(self):
        """Get the request."""
        return self._socket.accept()

    def do_GET(self):
        print("You did it")

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
