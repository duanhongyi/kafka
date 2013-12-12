import logging
import socket
import struct

from poolbase import pool, connection
from kafka.common import BufferUnderflowError
from kafka.common import ConnectionError

log = logging.getLogger("kafka")

DEFAULT_TIMEOUT = 10
DEFAULT_BUFFER_SIZE = 4096

class KafkaConnection(connection.Connection):
    """
    A socket connection to a single Kafka broker

    This class is _not_ thread safe. Each call to `send` must be followed
    by a call to `recv` in order to get the correct response. Eventually,
    we can do something in here to facilitate multiplexed requests/responses
    since the Kafka API includes a correlation id.
    """
    def __init__(self, host, port, **kwargs):
        connection.Connection.__init__(self)
        self.host = host
        self.port = port
        self.buffer_size = kwargs.get('buffer_size', DEFAULT_BUFFER_SIZE)
        self.auto_connect = kwargs.get('auto_connect', True)
        self._sock = None
        self.isOpen = False
        if self.auto_connect:
            self.open()
            self.isOpen = True

    def __str__(self):
        return "<KafkaConnection host=%s port=%d>" % (self.host, self.port)

    ###################
    #   Private API   #
    ###################

    def _consume_response(self):
        """
        Fully consumer the response iterator
        """
        data = ""
        for chunk in self._consume_response_iter():
            data += chunk
        return data

    def _consume_response_iter(self):
        """
        This method handles the response header and error messages. It
        then returns an iterator for the chunks of the response
        """
        log.debug("Handling response from Kafka")

        # Read the size off of the header
        resp = self._sock.recv(4)
        if resp == "":
            self._raise_connection_error()
        (size,) = struct.unpack('>i', resp)

        message_size = size - 4
        log.debug("About to read %d bytes from Kafka", message_size)

        # Read the remainder of the response
        total = 0
        while total < message_size:
            resp = self._sock.recv(self.buffer_size)
            log.debug("Read %d bytes from Kafka", len(resp))
            if resp == "":
                raise BufferUnderflowError(
                    "Not enough data to read this response")

            total += len(resp)
            yield resp

    def _raise_connection_error(self):
        self.isOpen = False
        error_message = "Kafka @ {}:{} went away".format(self.host, self.port)
        raise ConnectionError(error_message)

    ##################
    #   Public API   #
    ##################
    def open(self):
        if self.isOpen:
            return
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self.host, self.port))
        self._sock.settimeout(DEFAULT_TIMEOUT)
        self.isOpen = True

    def push(self, request_id, payload):
        "Push a request to Kafka, Does not require response"
        log.debug("About to send %d bytes to Kafka, request %d" % (
            len(payload), request_id))
        try:
            if not self.isOpen:
                self.refresh()
            sent = self._sock.sendall(payload)
            if sent is not None:
                self._raise_connection_error()
        except socket.error:
            log.exception('Unable to send payload to Kafka')
            self._raise_connection_error()

    def request(self, request_id, payload):
        """
        Send request and get a response from Kafka
        """
        log.debug("Reading response %d from Kafka" % request_id)
        self.push(request_id, payload)
        return self._consume_response()

    def close(self):
        """
        Close this connection
        """
        if self._sock:
            self._sock.close()

    def refresh(self):
        """
        Re-initialize the socket connection
        """
        self.close()
        self.open()


class KafkaConnectionPool(pool.ConnectionPool):
    def __init__(self, size, **kwargs):
        pool.ConnectionPool.__init__(
            self,
            size,
            connection_klass=KafkaConnection,
            **kwargs
        )

    def push(self, request_id, payload):
        with self.connection() as conn:
            conn.push(request_id, payload)

    def request(self, request_id, payload):
        with self.connection() as conn:
            return conn.request(request_id, payload)
