#!/usr/bin/env python

import math
import random
import sys
import time

from DynamicWords import DynamicWords


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
  between Pushers and Pullers.  (See DynamicTags.Initialize (), below.)

'''

class DynamicTags (DynamicWords):

    _dynamicTags = {}

    @classmethod
    def Initialize (cls, tagsFile, refresh = 600):
        DynamicWords.Initialize (tagsFile, refresh)
    
    @classmethod
    def dynamicTagsFor (cls, static_tag, min_num_tags = 1, max_num_tags = 1):
        _dynamicTags = cls._dynamicTags.get (static_tag, None)
        if _dynamicTags is None:
            _dynamicTags = cls (static_tag, min_num_tags, max_num_tags)
            cls._dynamicTags[static_tag] = _dynamicTags
        
        return _dynamicTags
    
    def __init__ (self, static_tag, min_num_tags, max_num_tags):
        super ().__init__ (static_tag, min_num_tags, max_num_tags)
    
    def tags (self, interval = 0):
        return list (map (lambda _tag: '#' + _tag, self.words (interval)))


def main ():
    DynamicTags.Initialize ('../config/wordlist.txt', 5)

    _static_tag   = sys.argv[1] if len (sys.argv) > 1 else "secret"
    _dynamic_tags = DynamicTags.dynamicTagsFor (_static_tag, 3, 5)
    
    for _ in range (0, 15):
        print (list (map (_dynamic_tags.tags, [-2, -1, 0])))
        time.sleep (6)

if __name__ == "__main__":
    main ()
