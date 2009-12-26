import socket

class DragonbellyError(Exception): pass
class ConnectionError(DragonbellyError): pass

class Dragonbelly(object):
    """
    The main Dragonbelly class.
    """

    def __init__(self, host=None, port=None, domain=None):
        self.host = host or 'localhost'
        self.port = port or 6565
        self.domain = domain
        self._sock = None
        self._fp = None

    def _write(self, data):
        try:
            self._sock.sendall(data)
        except socket.error, e:
            if e.args[0] == 32:
                # broken pipe
                self.disconnect()
            raise ConnectionError("Error %s while writing to socket. %s." % tuple(e.args))

    def _read(self):
        try:
            return self._fp.readline()
        except socket.error, e:
            if e.args and e.args[0] == errno.EAGAIN:
                return
            self.disconnect()
            raise ConnectionError("Error %s while reading from socket. %s." % tuple(e.args))

    def connect(self):
        """
        Connect to the dragonbelly daemon and select the right db.
        """
        if isinstance(self._sock, socket.socket):
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
        except socket.error, e:
            raise ConnectionError("Error %s connecting to %s:%s. %s." % (e.args[0], self.host, self.port, e.args[1]))
        else:
            self._sock = sock
            self._fp = self._sock.makefile('r')

    def disconnect(self):
        """
        Disconnect from the dragonbelly daemon.
        """
        if isinstance(self._sock, socket.socket):
            try:
                self._sock.close()
            except socket.error:
                pass
        self._sock = None
        self._fp = None

    def get_response(self):
        data = self._read().strip()
        if not data:
            self.disconnect()
            raise ConnectionError("Socket closed on remote end")

    def get(self, uri, domain):
        s = "GET %s HTTP/1.1\r\nHost: %s\r\n" % (uri, domain)
        self.connect()
        self._write(s)
        return self.get_response()
