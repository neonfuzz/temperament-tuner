#!/bin/env python3


"""
Provide an easy framework to tune an instrument.

Classes:
    Tuner - tuning class; `loop` will run the algorithm

When run:
    Will load the "Just" temperament for octaves 4, 5, and 6.
    Automaticall begins tuning.
"""


import matplotlib.pyplot as plt
import numpy as np
import pyaudio
from scipy.signal import find_peaks

from temperaments import JustTemperament


plt.rcParams["figure.figsize"] = (6, 18)


class Tuner:
    """
    Analyze input from an audio source.

    Methods:
        loop - Run the main loop; read in audio and process. Calls `graph`.
        fft - Perform an FFT on `data`
        graph - Graph the current `data` in different forms. Calls `fft`.

    Instance variables:
        format - audio format, default `pyaudio.paFloat32`
        channels (int) - number of channels to read, default 1
        rate (int) - audio rate, default 16000
        chunk (int) - how often to read audio and calculate `fft`, default 2048
        start_thresh (float 0-1) - noise must be above this threshold to be
                                   processed, default 0.1
        temperament (temperaments.Temperament) - Tuning temperament to use,
                                                 default JustTemperament
    """
    def __init__(self, **kwargs):
        """
        Optional Arguments:
            format - audio format, default `pyaudio.paFloat32`
            channels (int) - number of channels to read, default 1
            rate (int) - audio rate, default 16000
            chunk (int) - how often to read audio and calculate `fft`,
                default 2048
            start_thresh (float 0-1) - noise must be above this threshold
                to be processed, default 0.05
            temperament (temperaments.Temperament) - Tuning temperament to
                use, default JustTemperament
        """
        self.format = pyaudio.paFloat32
        self.channels = 1
        self.rate = 16000
        self.chunk = 2048
        self.start_thresh = 0.05
        self.temperament = JustTemperament()
        for key, value in kwargs.items():
            self.__dict__[key] = value

        self._pyaudio = pyaudio.PyAudio()
        self._data = np.array([])
        self._best_freq = np.array([])

    def loop(self):
        """
        Run the main tuner loop until `KeyboardInterrupt`.

        While True:
            read input from audio source
            analyze FFT of data
            plot to screen
        """
        stream = self._pyaudio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            output=False,
            frames_per_buffer=self.chunk)

        try:
            while True:
                audio = stream.read(self.chunk)
                audio = np.frombuffer(audio, np.float32)
                if audio.max() > self.start_thresh:
                    self._data = np.append(self._data, audio)
                    self.graph()
                else:
                    self._data = np.array([])
                    self._best_freq = np.array([])
        except KeyboardInterrupt:
            self._pyaudio.close(stream)

    def fft(self):
        """Calculate the FFT of `data`."""
        fft = np.fft.fft(self._data, n=self.rate).real
        frequencies = np.fft.fftfreq(len(fft)) * self.rate
        return frequencies, fft

    def graph(self):
        """
        Plot `data` from audio input.
        
        Two sub-plots:
            Waveform: amplitude vs time
            Frequency spectrum: amplitude vs frequency
                "best" frequency is indicated with a dashed vertical line
                and a text label indicating the tone and cents sharp/flat
        """
        # pylint: disable=invalid-name
        # 'xs' is a totally valid name for x-data.
        plt.clf()

        # Plot waveform.
        plt.subplot(211)
        xs = np.arange(0, len(self._data)) / self.rate
        plt.plot(xs, self._data)
        plt.xlabel('time (s)')
        plt.ylabel('amplitude')

        # Plot frequency spectrum.
        freqs, fft = self.fft()
        plt.subplot(212)
        plt.plot(freqs, fft)
        plt.xlim([self.temperament.frequencies.min()-100,
                  self.temperament.frequencies.max()+100])
        plt.ylim(bottom=0)
        plt.xlabel('frequency (Hz)')
        plt.ylabel('amplitude')

        # Identify peaks.
        peaks, _ = find_peaks(fft, height=min(25, fft.max()/2), distance=200)
        peaks = peaks[:len(peaks)//2]
        peak_freqs = freqs[peaks]
        peak_amps = fft[peaks]
        for freq, amp in zip(peak_freqs, peak_amps):
            if amp == peak_amps.max():
                self._best_freq = np.append(self._best_freq, freq)
            desired_idx = np.abs(self.temperament.frequencies-freq).argmin()
            desired_freq = self.temperament.frequencies[desired_idx]
            desired_note = self.temperament.notes[desired_idx]
            try:
                cents = int(1200 * np.log2(freq/desired_freq))
            except OverflowError:
                cents = 0

            # Plot local maximum on frequency spectrum.
            xs = np.array([freq, freq])
            ys = np.array([0, amp])
            plt.plot(xs, ys, color='red')

            # Label peak with nearest note and cents sharp/flat.
            sign = '+' if cents > 0 else ''
            note_str = '%s %s%s' % (desired_note, sign, cents)
            if amp == peak_amps.max():
                print(note_str)
            plt.text(freq+20, amp-5, note_str, fontsize=16)

        # Keep things looking nice; don't update too often.
        plt.tight_layout()
        plt.pause(0.01)


if __name__ == '__main__':
    TEMPERAMENT = JustTemperament(min_octave=4, max_octave=6)
    TUNER = Tuner(temperament=TEMPERAMENT)
    TUNER.loop()
