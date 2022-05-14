import select
import serial
import struct
import time
import lcm

from collections import deque

from scipy.signal import convolve
from numpy import ones

from ..lcmtypes.raw import floats_t
from ..lcmtypes.marine_sensor import radiometer_t
# downwelling_photon_spherical_irradiance mol m-2 s-1
# | downwelling_photon_flux_in_sea_water mol m-2 s-1
# | downwelling_photon_radiance_in_sea_water mol m-2 s-1 sr-1
# + bioluminescent_photon_rate_in_sea_water s-1 m-3


# TODO: This FIR minimizer and the other estimator should both be subclasses of
# a general estimator class.
class FIRMinimizer:

    def __init__(self, suffix = 'u', npackets=200, ntaps=50, f=0.95, verbose=0):
        self.lcm = lcm.LCM()
        self.suffix = suffix
        self.npackets = npackets
        self.data = deque(maxlen=2*ntaps)
        self.minima = deque(maxlen=npackets)
        self.window = ones(ntaps) / ntaps
        self.verbose = verbose

    def estimate_ambient(self,):
        """Estimate the ambient *downwelling_photon_spherical_irradiance*

        This does the heavy lifting.
        """
        filtered = convolve(self.data, self.window, mode='valid')
        # assert len(filtered) == ntaps + 1
        self.minima.append(min(filtered))
        return min(self.minima)

    def handler(self, channel, data):
        rx = floats_t.decode(data)
        self.data.extend(rx.data)
        if len(self.data) == self.data.maxlen:
            tx = radiometer_t()
            tx.utime = rx.utime
            tx.downwelling_photon_spherical_irradiance = self.estimate_ambient()
            if self.verbose > 0:
                print(tx.downwelling_photon_spherical_irradiance)
            tx_channel = "{0}{1}".format(channel[:4], self.suffix)
            self.lcm.publish(tx_channel, tx.encode())
        elif self.verbose > -1:
            print("window not full: {0} < {1}".format(len(self.data),
                self.data.maxlen))

    def filter(self, channel='RAD1fd'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()


def main(channel='RAD1fd', suffix='u', width=40, packets=200, taps=50, verbose=0):
    """Run as a daemon."""
    est = FIRMinimizer(suffix=suffix, npackets=packets, ntaps=taps, verbose=verbose)
    est.filter(channel);


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
    p.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    p.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    p.add_argument('-c', '--channel', default='RAD1fd',
                   help='channel to listen on')
    p.add_argument('-s', '--suffix', default='u',
                   help='suffix for filter output')
    p.add_argument('-w', '--width', type=int, default=40,
                   help='window width in ensembles')
    p.add_argument('-t', '--taps', type=int, default=50,
                   help='number of samples in inner window (filter taps)')
    p.add_argument('-p', '--packets', type=int, default=200,
                   help='number of packets in outer window')

    a = p.parse_args()
    main(**a.__dict__)
