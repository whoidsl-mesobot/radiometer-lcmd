#!/usr/bin/env python3

import argparse
from .ambient_downwelling_photon_flux_estimator import AmbientDownwellingPhotonFluxEstimator, DEFAULT_SORT_WIDTH
# from .fir_minimizer import 

p = argparse.ArgumentParser(description="LCM daemon to filter radiometer data")
p.add_argument('-v', '--verbose', action='count', default=0,
               help='display verbose output')
p.add_argument('-V', '--version', action='version',
               version='%(prog)s 0.0.1',
               help='display version information and exit')
p.add_argument('-c', '--channel', default='RAD1t',
               help='channel to listen on')
p.add_argument('-s', '--suffix', default='u',
               help='suffix for filter output')
p.add_argument('-w', '--width', type=int, default=DEFAULT_SORT_WIDTH,
               help='window width in ensembles')

args = p.parse_args()
est = AmbientDownwellingPhotonFluxEstimator(**args.__dict__)
est.filter(args.channel);
