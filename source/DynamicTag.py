#!/usr/bin/env python

import math
import random
import sys
import time

from DynamicWord import DynamicWord


'''

Considerations:

- Is random deterministic?
  - https://docs.python.org/3/library/random.html states
    "Python uses the Mersenne Twister as the core generator....
     The underlying implementation in C is both fast and threadsafe.
     The Mersenne Twister is ... completely deterministic...."

- Save/restore random state (for other users); concurrent threads are a _problem_!
  - https://docs.python.org/3/library/random.html states
    "The functions supplied by this module are actually bound methods of
     a hidden instance of the random.Random class. You can instantiate
     your own instances of Random to get generators that don't share state."
  - Solution: create separate rand.Random instances.

- Collisions
  - Unfortunately, we cannot guarantee tag uniqueness between
    Pushers.  Consequently, downstream Pullers may pull
    "misaddressed" postings.

- Widen the tag duration window to permit implicit synchronization
  between Pushers and Pullers.  (See DynamicTag.Initialize (), below.)

'''

class DynamicTag (DynamicWord):

    _dynamicTags = {}

    @classmethod
    def Initialize (cls, tagsFile, refresh = 600):
        DynamicWord.Initialize (tagsFile, refresh)
    
    @classmethod
    def dynamicTagFor (cls, static_tag):
        _dynamicTag = cls._dynamicTags.get (static_tag, None)
        if _dynamicTag is None:
            _dynamicTag = cls (static_tag)
            cls._dynamicTags[static_tag] = _dynamicTag
        
        return _dynamicTag
    
    def __init__ (self, static_tag):
        super ().__init__ (static_tag)
    
    def tag (self, interval = 0):
        return '#' + self.word (interval)


def main ():
    DynamicTag.Initialize ('../config/wordlist.txt', 5)

    _static_tag  = sys.argv[1] if len (sys.argv) > 1 else "secret"
    _dynamic_tag = DynamicTag.dynamicTagFor (_static_tag)
    
    for _ in range (0, 15):
        print (list (map (_dynamic_tag.tag, [-2, -1, 0])))
        time.sleep (6)

if __name__ == "__main__":
    main ()
