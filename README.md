# temperament-tuner
Tune any instrument using any temperament with immediate graphical feedback.

Basic use (octaves 4, 5, 6 with "Just" tuning):
```./tuner.py```


More advanced use:
```
from temperaments import EqualTemperament
from tuner import Tuner

TUNER = Tuner(temperament=EqualTemperament())
TUNER.loop()
```

See `temperaments.py` for a list of all pre-coded temperaments.
See `tuner.py` for all tuner options, including channels, audio rate, etc.
