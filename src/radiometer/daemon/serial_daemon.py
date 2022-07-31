"""radiometer_lcmd - LCM daemon for radiometer."""

import select
import serial
import struct
import time
import lcm

from collections import deque

from ..lcmtypes.raw import bytes_t, floats_t


class SerialDaemon:
    """Serial LCM daemon for radiometer."""

    def __init__(self, dev='/dev/ttyUSB1', prefix='RAD'):
        """Define serial and LCM interfaces, and subscribe to input."""
        self.serial = serial.Serial(dev, baudrate=38400, timeout=1)
        self.lcm = lcm.LCM()
        self.prefix = prefix + dev[-1]
        self.tkn = deque(maxlen = 4)
        self.heartbeat = struct.Struct('<7L') # 7 uint32 (UTC, millis, Pulse count, nsHI, irradiance, inclinometer, end token)
        self.data = struct.Struct('<2L50H') # 2 uint32 (ISR clock cycles, LOG clock cycles), then 50 uint16

        self.subscriptions = []
        self.subscriptions.append(self.lcm.subscribe(
            '{0}i'.format(self.prefix), self.lcm_handler))

    def lcm_handler(self, channel, data):
        """Receive command on LCM and send over serial port.

        Initially, this will pass opaque byte streams.
        Later, we may refactor for more user-friendly LCM messages.
        """
        rx = raw.bytes_t.decode(data)
        print("rx on LCM {0}: {1}".format(channel, rx.data))
        self.serial.write(rx.data)
        self.serial.flush()

    def serial_handler(self):
        """Receive data on serial port and send on LCM."""
        pkt_size = 0
        while self.serial.in_waiting > 0 and pkt_size == 0:
            try_bytes = max(self.tkn.maxlen - len(self.tkn), 1)
            self.tkn.extend(self.serial.read(try_bytes))
            bsh = bytes(self.tkn)
            if bsh == bytes.fromhex('FDFDFDFD'):
                suffix = 'o'
                pkt_size = self.data.size
            elif bsh == bytes.fromhex('FEFEFEFE'):
                suffix = 'h'
                pkt_size = self.heartbeat.size
            else:
                suffix = 'r'
                pkt_size = 0
            self.handle_pkt(suffix, pkt_size)

    def handle_pkt(self, suffix='r', sz=0):
        rx = self.serial.read(sz)
        if(len(rx) == sz):
            tx = bytes_t()
            tx.utime = int(time.time() * 1e6)
            tx.length = len(self.tkn) + sz
            tx.data = bytes(self.tkn) + rx
            self.lcm.publish("{0}{1}".format(self.prefix, suffix), tx.encode())
            if(suffix == 'o' and sz == self.data.size):
                self.publish(tx)
        else:
            print('tried to read {0} but only got {1}'.format(sz, len(rx)))

    def publish(self, raw, tsuffix='t', psuffix='p'):
        tx = floats_t()
        tx.utime = raw.utime
        b = raw.data[4:] # assert len(b) = self.data.size
        tx.data = [x * 16 for x in self.data.unpack(b)[2:]] # skip the extras
        tx.length = len(tx.data) # assert = 50
        self.lcm.publish("{0}{1}".format(self.prefix, tsuffix), tx.encode())
        tx.data = [x * 1e-4 for x in tx.data]
        self.lcm.publish("{0}{1}".format(self.prefix, psuffix), tx.encode())

    def connect(self):
        """Connect serial to LCM and loop with epoll."""
        epoll = select.epoll()
        epoll.register(self.lcm.fileno(), select.EPOLLIN)
        epoll.register(self.serial.fileno(), select.EPOLLIN)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        try:
            while True:
                for fileno, _events in epoll.poll(1):
                    if fileno == self.lcm.fileno():
                        self.lcm.handle()
                    elif fileno == self.serial.fileno():
                        self.serial_handler()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
        finally:
            epoll.unregister(self.serial.fileno())
            epoll.unregister(self.lcm.fileno())
            epoll.close()
