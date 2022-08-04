#!/usr/bin/env python3
"""LCM daemons for radiometer."""

from .serial_daemon import SerialDaemon

def main(dev="/dev/ttyUSB1", prefix='RAD', verbose=0):
    """Run as a daemon."""
    print('verbose={}'.format(verbose))
    bridge = SerialDaemon(dev, prefix, verbose)
    bridge.connect()


if __name__ == "__main__":
    import argparse
    P = argparse.ArgumentParser(description="serial LCM daemon for radiometer")
    P.add_argument('-v', '--verbose', action='count', default=0,
                   help='display verbose output')
    P.add_argument('-V', '--version', action='version',
                   version='%(prog)s 0.0.1',
                   help='display version information and exit')
    P.add_argument('dev', help='the serial device to use')
    P.add_argument('-p', '--prefix', default='RAD',
                   help='prefix to pub/sub with')
    A = P.parse_args()
    main(**A.__dict__)
