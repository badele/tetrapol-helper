#!/usr/bin/python3
# Source: from tetrahub site(syracuse & seewhy)


""" v0614 """
import sys
import math
import time
import threading
import subprocess
from argparse import ArgumentParser
import osmosdr
from gnuradio import gr, blocks, filter, digital, analog

DIR_DICT = {1: 390235000,
            690: 390275000,
            602: 408005000,
            603: 408015000,
            604: 408025000,
            607: 408035000,
            613: 408045000,
            614: 408055000,
            617: 408065000,
            618: 408075000,
            623: 408085000,
            624: 408095000,
            612: 408105000,
            628: 408115000,
            433: 408125000,
            634: 408135000,
            643: 408145000,
            644: 408155000,
            653: 408165000,
            654: 408175000,
            663: 408185000,
            622: 408195000,
            702: 408275000,
            703: 408285000,
            704: 408295000,
            713: 408315000,
            714: 408325000,
            723: 408355000,
            724: 408365000,
            712: 408375000,
            733: 408395000,
            734: 408405000,
            722: 409595000,
            743: 409605000,
            744: 409615000,
            753: 409625000,
            754: 409635000,
            763: 409645000,
            764: 409655000,
            773: 409665000,
            774: 409675000,
            775: 409685000,
            732: 409695000,
            783: 409705000,
            784: 409715000,
            785: 409725000,
            632: 409895000,
            664: 409915000,
            673: 409935000,
            674: 409955000,
            675: 409965000,
            683: 409975000,
            684: 409985000,
            685: 409995000,
            609: 383675000,
            619: 393680000,
            610: 380215000,
            620: 380225000,
            630: 380235000,
            640: 380255000}


class TopBlock(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        options = get_options()

        bitrate = 8000
        chan0_freq = int()
        # channel_bw = options.channel_bandwidth
        if options.network == "INPT":
            chan0_freq = 368645000  # 368644500
        elif options.network == "Rubis":
            chan0_freq = 40965000  # 40960000

        self.rfgain = options.gain

        self.channels = [int(ch) for ch in options.channels.split(',') if ch]
        if options.network == "INPT" or options.network == "Rubis":
            self.ch_freqs = [ch * 10000 + chan0_freq for ch in self.channels]
        elif options.network == "DIR":
            self.ch_freqs = [DIR_DICT[ch] for ch in self.channels]

        self.ch_freqs.extend([int(f) for f in options.channels_by_freq.split(',') if f])
        while len(self.channels) < len(self.ch_freqs):
            self.channels.append(-1)

        if options.frequency is None:
            self.ifreq = (max(self.ch_freqs) + min(self.ch_freqs)) / 2
        else:
            self.ifreq = options.frequency

        self.src = osmosdr.source(options.args)
        self.src.set_center_freq(self.ifreq)
        self.src.set_sample_rate(options.sample_rate)
        self.src.set_freq_corr(options.ppm, 0)

        if self.rfgain is None:
            self.src.set_gain_mode(True, 0)
            self.iagc = 1
            self.rfgain = 0
        else:
            self.iagc = 0
            self.src.set_gain_mode(False)
            self.src.set_gain(self.rfgain)
            self.src.set_if_gain(37)

        # may differ from the requested rate
        sample_rate = int(self.src.get_sample_rate())
        sys.stdout.write("sample rate: %d\n" % sample_rate)

        first_decim = int(options.sample_rate / bitrate / 2)
        sys.stdout.write("decim: %d\n" % first_decim)

        out_sample_rate = sample_rate / first_decim
        sys.stdout.write("output sample rate: %d\n" % out_sample_rate)

        sps = out_sample_rate / bitrate
        sys.stdout.write("samples per symbol: %d\n" % sps)

        self.tuners = []
        self.afc_probes = []
        if len(self.channels) != 1:
            if options.output_file:
                if options.output_file.find('%%') == -1:
                    raise ValueError('Output name template missing "%%".')
            elif options.output_pipe:
                if options.output_pipe.find('%%') == -1:
                    raise ValueError('Output name template missing "%%".')
            else:
                raise ValueError('WTF')
        for ch in range(0, len(self.channels)):
            bw = (9200 + options.afc_ppm_threshold) / 2
            taps = filter.firdes.low_pass(1.0, sample_rate, bw, bw * options.transition_width, filter.firdes.WIN_HANN)
            offset = self.ch_freqs[ch] - self.ifreq
            sys.stdout.write(
                "channel[%d]: %d frequency=%d, offset=%d Hz\n" % (ch, self.channels[ch], self.ch_freqs[ch], offset))

            tuner = filter.freq_xlating_fir_filter_ccc(first_decim, taps, offset, sample_rate)
            self.tuners.append(tuner)

            demod = digital.gmsk_demod(samples_per_symbol=sps)

            fname = self.channels[ch]
            if fname == -1:
                fname = self.ch_freqs[ch]
            if options.output_pipe is None:
                file = options.output_file.replace('%%', str(fname))
                output = blocks.file_sink(gr.sizeof_char, file)
                if options.debug == "True":
                    file_debug = options.output_file.replace('%%', str(fname) + "debug")
                    self.output_debug = blocks.file_sink(gr.sizeof_char, file_debug)
            else:
                cmd = options.output_pipe.replace('%%', str(fname))
                pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)
                fd = pipe.stdin.fileno()
                output = blocks.file_descriptor_sink(gr.sizeof_char, fd)

            self.connect((self.src, 0), (tuner, 0))
            self.connect((tuner, 0), (demod, 0))
            self.connect((demod, 0), (output, 0))
            if options.debug == "True":
                self.connect((demod, 0), (self.output_debug, 0))

            afc_decimation = 32000
            afc_demod = analog.quadrature_demod_cf(sample_rate / first_decim / (2 * math.pi * afc_decimation))
            integrate = blocks.integrate_ff(afc_decimation)
            afc_probe = blocks.probe_signal_f()
            self.afc_probes.append(afc_probe)

            self.connect((tuner, 0), (afc_demod, 0))
            self.connect((afc_demod, 0), (integrate, 0))
            self.connect((integrate, 0), (afc_probe, 0))

        def _variable_function_probe_0_probe():
            while True:
                time.sleep(options.afc_period)
                for ch in range(0, len(self.channels)):
                    err = self.afc_probes[ch].level()
                    if abs(err) < options.afc_ppm_threshold:
                        continue
                    freq = self.tuners[ch].center_freq() + err * options.afc_gain
                    self.tuners[ch].set_center_freq(freq)
                    if self.channels[ch] == -1:
                        sys.stdout.write("Freq %d freq err: %5.0f\tfreq: %f\n" % (self.ch_freqs[ch], err, freq))
                    else:
                        sys.stdout.write("Chan %d freq err: %5.0f\tfreq: %f\n" % (self.channels[ch], err, freq))
                sys.stdout.write(("📡  "*15).center(40) + "\n")

        _variable_function_probe_0_thread = threading.Thread(target=_variable_function_probe_0_probe)
        _variable_function_probe_0_thread.daemon = True
        _variable_function_probe_0_thread.start()


def get_options():
    parser = ArgumentParser()
    parser.add_argument("-a", "--args", type=str, default="", help="gr-osmosdr device arguments", required=True)
    parser.add_argument("-s", "--sample-rate", type=float, default=1024000,
                        help="receiver sample rate (default: 1024000)")
    parser.add_argument("-f", "--frequency", type=float, default=None,
                        help="receiver center frequency")
    parser.add_argument("-g", "--gain", type=float, default=None, help="set receiver gain")
    parser.add_argument("-B", "--channel_bandwidth", type=float, default=10000,
                        help="set channel bandwidth (12500 or 10000)")
    parser.add_argument("-c", "--channels", type=str, default="", help="channel numbers")
    parser.add_argument("-p", "--ppm", dest="ppm", type=float, default=0, help="Frequency correction")
    parser.add_argument("-t", "--transition-width", type=float, default=0.2,
                        help="low pass transition width (default: 0.2")
    parser.add_argument("-G", "--afc-gain", type=float, default=0.2, help="afc gain (default: 0.2)")
    parser.add_argument("-P", "--afc-period", type=float, default=2, help="afc period (default: 2)")
    parser.add_argument("-T", "--afc-ppm-threshold", type=float, default=100, help="afc threshold (default: 100)")
    parser.add_argument("-o", "--output-file", type=str, default="channel%%.bits", help="specify the bit output file")
    parser.add_argument("-O", "--output-pipe", type=str, default=None, help="specify shell pipe to send output")
    parser.add_argument("-l", "--channels-by-freq", type=str, default="", help="Receive on specified frequencies")
    parser.add_argument("-n", "--network", type=str, default="INPT", help="Network: INPT, DIR or Rubis")
    parser.add_argument("-d", "--debug", type=str, default="False", required=False, help="Debug mode")
    options = parser.parse_args()

    return options


if __name__ == '__main__':
    tb = TopBlock()
    tb.start()
    tb.wait()
