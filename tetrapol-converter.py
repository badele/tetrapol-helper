#!/usr/bin/env python3

import re
import sys

import tools

from argparse import ArgumentParser

APPLICATION_NOM = "Tetra frequencies converter"

def get_options():
    parser = ArgumentParser()
    parser.add_argument("-c", "--channel", type=int, default=0, help="Channel Id", required=False)
    parser.add_argument("-f", "--freq", type=str, default="", help="Freq in Mhz", required=False)
    parser.add_argument('-v', '--version', action='version', version=f'{tools.__name__} {tools.__version__} - %(prog)s - {APPLICATION_NOM}')

    if len(sys.argv)==1:
        parser.print_help()

    options = parser.parse_args()

    return options


if __name__ == '__main__':
    options = get_options()

    if options.channel and options.freq:
        print("Please choose only one option [-c/--channel] or [-f/--freq]")
        sys.exit()

    # Convert to channel Id
    if options.freq:
        freqhz = tools.freqToHz(options.freq)

        channel = tools.convertFreqToChannel(freqhz)
        print(f"{tools.freqToStr(tools.freqToHz(options.freq))} => {channel}")

    # Convert channel to Frequency
    if options.channel:

        freqhz = tools.convertChannelToFreq(int(options.channel))

        print(f"{options.channel} => {tools.freqToStr(freqhz)}")