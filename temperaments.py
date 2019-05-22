

"""
Provides many different historical temperaments for tuning.

Variables:
    TONES - piano key note names from 'C' to 'B'; half tones are all #.

Classes:
    Note - store information about a note's tone, octave, and frequency
    Temperament - base class meant to be sub-classed
    EqualTemperament - equal spacing between all tones
    JustTemperament - most pure ratios for the "white keys"
    PythagoreanTemperament - pre-Renaissance, optimized for major fifths
    MeanToneTemperament - Renaissance, optimize for major thirds
    WellTemperament - Bach's temperament
    RameauTemperament - Modification of meantone to eliminate most "wolf" notes
    WerckmeisterITemperament - Best thirds in keys with fewest incidentals
    KirnbergerIIITemperament - Most fifths are pure or very close to pure.
    VallottiYoungTemperament - Elegant take on well-temperament.
"""


import numpy as np


TONES = [
    'C',
    'C#',
    'D',
    'D#',
    'E',
    'F',
    'F#',
    'G',
    'G#',
    'A',
    'A#',
    'B',
    ]


class Note():
    """
    Store information about a single note.

    Instance variables:
        tone (str) - C-B tone
        octave (int) - pitch octave
        frequency (float or None) - frequency in Hz
    """
    def __init__(self, tone, octave, frequency=None):
        self.tone = tone
        self.octave = octave
        self.frequency = frequency

    def __repr__(self):
        return '%s%s' % (self.tone, self.octave)

    def __eq__(self, val):
        return self.__repr__() == val


class Temperament():
    """
    Base Temperament class meant to be sub-classed.

    Instance variables:
        name (str) - Name of the temperament
        reference_note (Note) - default A4
        reference_freq (float) - in Hz, default 440.0
        min_octave (int) - lowest octave to calculate, default 0
        max_octave (int) - highest octave to calculate, default 8
        ratios (np.array) - ratios between frequencies of TONES and TONES[0]
        cents (np.array) - same as `ratios` but measured in cents
        notes (list, read-only) - `Note` objects for the temperament
        frequencies (np.array, read-only) - frequencies (in Hz) for `notes`
    """
    def __init__(self, reference_note=Note('A', 4), reference_freq=440.,
                 min_octave=0, max_octave=8):
        self._name = ''
        self._reference_note = reference_note
        self._reference_freq = reference_freq
        self._min_octave = min_octave
        self._max_octave = max_octave
        self._notes = self._make_notes()

        self._ratios = np.array([])
        self._cents = np.array([])

    def __repr__(self):
        return '%s %s@%sHz' % (
            self._name, self._reference_note, self._reference_freq)

    @property
    def reference_note(self):
        """Note to equal `reference_freq`, default Note('A', 4)."""
        return self._reference_note

    @reference_note.setter
    def reference_note(self, note):
        if not isinstance(note, Note):
            raise ValueError(
                'Reference note must be of the "Note" type, not %s' % type(
                    note))
        self._reference_note = note
        self._calculate_frequencies()

    @property
    def reference_freq(self):
        """Frequency (in Hz) to set `reference_note`, default 440.0."""
        return self._reference_freq

    @reference_freq.setter
    def reference_freq(self, freq):
        self._reference_freq = freq
        self._calculate_frequencies()

    @property
    def min_octave(self):
        """Lowest octave to calculate, default 0."""
        return self._min_octave

    @min_octave.setter
    def min_octave(self, min_octave):
        self._min_octave = min_octave
        self._make_notes()
        self._calculate_frequencies()

    @property
    def max_octave(self):
        """Highest octave to calculate, default 8."""
        return self._max_octave

    @max_octave.setter
    def max_octave(self, max_octave):
        self._max_octave = max_octave
        self._make_notes()
        self._calculate_frequencies()

    @property
    def ratios(self):
        """Ratios between first tone and other tones."""
        return self._ratios

    @ratios.setter
    def ratios(self, ratios):
        self._ratios = np.array(ratios)
        self._cents = 1200 * np.log2(self._ratios)
        self._calculate_frequencies()

    @property
    def cents(self):
        """Cent values between first tone and other tones."""
        return self._cents

    @cents.setter
    def cents(self, cents):
        self._cents = np.array(cents)
        self._ratios = 2**(self._cents/1200)
        self._calculate_frequencies()

    @property
    def notes(self):
        """Notes calculated for the temperament."""
        return self._notes

    @property
    def frequencies(self):
        """Frequencies (in Hz) associated with `notes`."""
        return np.array([x.frequency for x in self._notes])

    def _make_notes(self):
        notes = []

        i = 0
        tone = 'C'
        octave = self._min_octave
        while octave < self._max_octave + 1:
            new_note = Note(tone, octave)
            if new_note == self._reference_note:
                new_note.frequency = self._reference_freq
            notes.append(new_note)
            i += 1
            if i == len(TONES):
                i = 0
                octave += 1
            tone = TONES[i]

        return notes

    def _calculate_base_freq(self):
        ref_idx = self.notes.index(self._reference_note) % len(self._ratios)
        oct_ratio = 2**(self.notes[0].octave - self._reference_note.octave)
        return oct_ratio * self._reference_freq / self._ratios[ref_idx]


    def _calculate_frequencies(self):
        self._notes[0].frequency = self._calculate_base_freq()
        i = 0
        oct_diff = 0
        for note in self._notes:
            ratio = self._ratios[i] * 2**(oct_diff)
            note.frequency = ratio * self._notes[0].frequency

            i += 1
            if i == len(self._ratios):
                i = 0
                oct_diff += 1


class EqualTemperament(Temperament):
    """
    Equal cent values between each tone.

    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Equal'
        self.cents = np.arange(0, 1200, 100)


class JustTemperament(Temperament):
    """
    Most pure ratios between "white keys."

    "Black keys" are calculated with 5-limit tuning.
    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._name = 'Just'
        self.ratios = np.array([
            1, 16/15, 9/8, 6/5, 5/4, 4/3, 64/45, 3/2, 8/5, 5/3, 19/9, 15/8])


class PythagoreanTemperament(Temperament):
    """
    Pre-Renaissance tuning to optimize pureness of major fifths.

    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Pythagorean'
        self.ratios = np.array([
            1, 256/243, 9/8, 32/27, 81/64, 4/3,
            729/512, 3/2, 128/81, 27/16, 16/9, 243/128])


class MeanToneTemperament(Temperament):
    """
    Renaissance-era tuning to create better major thirds.

    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Meantone'
        self.cents = np.array([
            0, 81.427, 194.135, 306.842, 388.270, 502.933,
            583.383, 697.067, 780.450, 891.202, 1004.888, 1085.338
            ])

class WellTemperament(Temperament):
    """
    Championed by Bach as an alternative to the meantone temperament.

    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Well-Tempered'
        self.cents = np.array([
            0, 90.225, 193.484, 294.135, 386.968, 498.045,
            588.270, 696.742, 792.180, 890.226, 996.090, 1088.923
            ])


class RameauTemperament(Temperament):
    """
    Developed by Rameau as a modification of the meantone temperament.

    Eliminates most of the "wolf" notes while maintaining most of
        meantone's pure harmonies.
    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Rameau'
        self.cents = np.array([
            0, 84.360, 192.180, 288.270, 384.360, 503.910,
            582.405, 696.090, 786.315, 888.270, 996.090, 1080.450
            ])


class WerckmeisterITemperament(Temperament):
    """
    Most popular temperament developed by Werckmeister.

    Developed in the 1600s to place the best thirds in the keys
        with the fewest incidentals.
    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Werckmeister I (III)'
        self.cents = np.array([
            0, 90.225, 192.180, 294.135, 390.225, 498.045,
            588.270, 696.090, 792.180, 888.270, 996.090, 1092.180
            ])


class KirnbergerIIITemperament(Temperament):
    """
    Most popular temperament developed by Kirnberger.

    Developed in 1776: most of the fifths are pure, with the exception
        of C-G, G-D, D-A, and A-E which are narrowed by 1/4 of the
        Pythagorean comma.
    Sub-classed from Temperament.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Kirnberger III'
        self.cents = np.array([
            0, 90.225, 203.910, 294.135, 386.315, 498.045,
            590.225, 701.955, 792.180, 884.360, 996.090, 1088.270
            ])


class VallottiYoungTemperament(Temperament):
    """
    Well-temperament scheme developed by Vallotti and Yound in 1779.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'Vallotti & Young'
        self.cents = np.array([
            0, 94, 196, 278, 392, 475, 588, 696, 790, 894, 975, 1090])
