"""
Use this to communicate with the TableSat

This module handles the interface between the the control system and either
the physical system or the theoretical model.  With the physical system, a
UDP socket is opened and either listens for packets transmitted from the
sensors or submits voltage packets to set actuator voltages.  When running
in simulations, the module submits and receives the voltage messages to
an in-memory model of the system that contains the system dynamics and can
return mocked sensor voltages based on the behavior.

**From Controller to Satellite**

* input: Voltage setting determined by the actuator
* output: UDP packet to the system or in-memory model

**From Satellite to Controller**

* input: Sensor voltages from the system or in-memory model
* output: Sensor data to submit to sensor class for conversion to a state

Example::

    def got_it(*args):
        print('got_it')

    import time
    bind_port = 9877
    send_to = ('127.0.0.1', 9878)
    u = UDP(bind_port, send_to)

    u.add_callback(104, got_it)

    with open('104.msg') as f:
        msg104 = f.read()
    with open('63.msg') as f:
        msg63 = f.read()
    with open('64.msg') as f:
        msg64 = f.read()

    u.send(104, 1)
    time.sleep(0.1)
    u.recieve()
    print(u.msg)

    u.send(104, 1)
    time.sleep(0.1)
    u.recieve()
    print(u.msg)

"""

import socket
import struct
import time
from io import BytesIO
from collections import defaultdict


def ReadAckMsg(msg):
    """
    A read ack message handler
    """
    return msg[0] == 1


def EndDataMsg(msg):
    """
    End of data message handler
    """
    pass


def ReadRawData(msg):
    """
    Raw data message handler
    """
    return [float(v) for v in msg]


# Define the prearranged message structure
MSG_HANDLERS = {
    2:   ['!B', 1, ReadAckMsg, 'Set run mode'],
    4:   ['!B', 1, None, 'Set run mode'],
    18:  ['!4d', 4 * 8, None, 'Set fan speed'],
    19:  ['!B', 1, None, 'Set log record mode'],
    20:  ['!B', 1, None, 'Request sensor reading'],
    22:  ['!B', 1, EndDataMsg, 'End of sensor log'],
    23:  ['!d', 8, None, 'Request sensor log data'],
    33:  ['!d', 8, None, 'Set log sample rate'],
    63:  ['!15d', 15 * 8, ReadRawData, 'Sensor readings'],
    64:  ['!16d', 16 * 8, ReadRawData, 'Sensor log entry'],
    65:  ['!d', 8, ReadRawData, 'Sensor log size'],
    104: ['!B', 1, ReadAckMsg, 'Ack run mode'],
    118: ['!B', 1, ReadAckMsg, 'Ack fan volt'],
    119: ['!B', 1, ReadAckMsg, 'Ack sensor log run mode'],
    133: ['!B', 1, ReadAckMsg, 'ACK log sample rate'],
}


class UDP_Err(Exception):
    pass


class UDP_Payload_Size(UDP_Err):
    pass


class UDP(object):
    """
    Define the UDP message interface.  Data gets packed in a [msglen][msgdata]
    structure in the same manner as a DNS packet.

    :param bind_port: receive UDP messages on this port
    :type  bind_port: integer
    :param send_to: the destination address (host, port)
    :type  send_to:
    """

    HEADER_FMT = '!5B'

    def __init__(self, bind_port, send_to):
        self.msg = {}
        self.callbacks = defaultdict(set)
        self.bind_port = bind_port

        self.send_to = send_to
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.sock.bind(('0.0.0.0', self.bind_port))
        self.sock.setblocking(0)

    def set_fan(self, v):
        """
        Helper method to send desired voltages
        """
        self.send(18, v)

    def send(self, msg_num, msg_data):
        packet = [msg_num, 0, 0, MSG_HANDLERS[msg_num][1], 0]
        packet.append(msg_data)
        print(packet)
        msg = struct.pack('BBBBBd', *packet)

        msg = msg_data
        self.sock.sendto(msg, self.send_to)

    def read_header(self, msgio):

        msg_num, flags, size1, size2, _ = struct.unpack(
            self.HEADER_FMT, msgio.read(5))

        payload_size = size1 * 1024 + size2

        if not payload_size == MSG_HANDLERS[msg_num][1]:
            err = 'Invalid payload size for msg num %s' % msg_num
            raise UDP_Payload_Size()

        return msg_num

    def read_payload(self, msg_num, msgio):
        fmt, payload_size, handler, name = MSG_HANDLERS[msg_num]

        # msg_data = struct.unpack_from('dddd', payload[1:])
        data_str = struct.unpack_from(fmt, msgio.read(payload_size))
        if handler is None:
            for callback in self.callbacks[msg_num]:
                callback()
        else:
            data = handler(data_str)
            self.msg[msg_num] = (time.time(), data)
            for callback in self.callbacks[msg_num]:
                callback(data)

    def recieve(self):
        try:
            while True:
                msg = self.sock.recv(1024)
                msgio = BytesIO(msg)
                msg_num = self.read_header(msgio)
                self.read_payload(msg_num, msgio)
        except socket.error:
            pass

    def add_callback(self, msg_num, callback):
        self.callbacks[msg_num].add(callback)

    def remove_callback(self, msg_num, callback):
        self.callbacks[msg_num].add(callback)
