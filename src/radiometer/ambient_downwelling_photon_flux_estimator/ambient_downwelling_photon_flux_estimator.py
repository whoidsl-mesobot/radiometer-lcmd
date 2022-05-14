"""Bioluminescence filter for Future Ocean Lab radiometer data

    Filters out spikes from bioluminescent events to give the ambient irradiance.
"""

import select
import time

from numpy import log10

import lcm

from collections import deque

from ..lcmtypes.raw import floats_t
from ..lcmtypes.marine_sensor import radiometer_t
# downwelling_photon_spherical_irradiance mol m-2 s-1
# | downwelling_photon_flux_in_sea_water mol m-2 s-1
# | downwelling_photon_radiance_in_sea_water mol m-2 s-1 sr-1
# + bioluminescent_photon_rate_in_sea_water s-1 m-3

SAMPLES_PER_ENSEMBLE = 50
DEFAULT_SORT_WIDTH = 200 # 200 ensembles @ 20 Hz ==> 10s
DEFAULT_SUM_WIDTH = 20 # 20 ensembles @ 20 Hz ==> 1s


class AmbientDownwellingPhotonFluxEstimator:

    def __init__(self, suffix = 'u', width=DEFAULT_SORT_WIDTH, verbose=0, **kw):
        self.lcm = lcm.LCM()
        self.data = deque(maxlen=width*SAMPLES_PER_ENSEMBLE)
        self.suffix = suffix
        self.verbose = verbose

    def estimate_ambient(self):
        """Estimate the ambient *downwelling_photon_spherical_irradiance*

        This does the heavy lifting.
        """
        tosort = list(self.data.copy())
        tosort.sort()
        amb = float(sum(tosort[:DEFAULT_SUM_WIDTH*SAMPLES_PER_ENSEMBLE]))
        return max([amb, 16]) # make output log10-safe
        # use sixteen here^ to match what would be a single timeHi count decoded

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
            
            lx = floats_t()
            lx.utime = rx.utime
            lx.data = [log10(tx.downwelling_photon_spherical_irradiance)]
            # TODO: consider returning 1 instead of log10(16) to emphasize RAD1t out of bounds
            lx.length = len(lx.data)
            lx_channel = "log{0}{1}".format(channel[:4], self.suffix)
            self.lcm.publish(lx_channel, lx.encode())

        elif self.verbose > -1:
            print("window not full: {0} < {1}".format(len(self.data),
                self.data.maxlen))

    def filter(self, channel='RAD1fd'):
        """Connect to LCM and handle."""

        subscription = self.lcm.subscribe(channel, self.handler)
        if self.verbose > 0:
            print("subscribed to: {0}".format(channel))
        try:
            while True:
                self.lcm.handle()
        except (KeyboardInterrupt, SystemExit):
            print('stopped by user')
            subscription.unsubscribe()
