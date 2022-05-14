import select
import serial
import struct
import time
import lcm

from ..lcmtypes.raw import floats_t


class Transformer:

    def __init__(self, verbose=0):
        self.lcm = lcm.LCM()
        self.verbose = verbose
        self.suffix = 'fd' # flux density

    def handler(self, channel, data):
        """receive time high and publish percent 
        """
        rx = floats_t.decode(data)
        rx.data = self.transform(rx.data)
        self.lcm.publish("{0}{1}".format(channel[:4], self.suffix), rx.encode())

    def go(self, channel='RAD1t'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        if(self.verbose > 0):
            print("subscribed to {0}".format(channel))
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()

    def transform(self, x):
        """This is the heavy lifter, but we don't know the transform yet.
        """
        return x
