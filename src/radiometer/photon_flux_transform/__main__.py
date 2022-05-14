#!/usr/bin/env python3

import argparse
from .photon_flux_transform import Transformer

p = argparse.ArgumentParser(description="LCM daemon to transform radiometer data")
p.add_argument('-v', '--verbose', action='count', default=0,
               help='display verbose output')
p.add_argument('-V', '--version', action='version',
               version='%(prog)s 0.0.1',
               help='display version information and exit')
p.add_argument('-c', '--channel', default='RAD1t',
               help='channel to listen on')
args = p.parse_args()

OptimusPrime = Transformer(verbose=args.verbose)
OptimusPrime.go(args.channel);
