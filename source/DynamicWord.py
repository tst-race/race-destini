#!/usr/bin/env python

import hashlib
import math
import random
import sys
import time


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

'''

class DynamicWord (object):
    _REFRESH_INTERVAL = 60 * 10     # 10 minute refresh (see Initialize (), below)

    _word_list    = None
    _l_word_list  = 0

    _dynamicWords = {}

    @classmethod
    def Initialize (cls, wordsFile, refresh = 600):
        with open (wordsFile) as _f:
            cls._word_list   = _f.read ().splitlines ()
            cls._l_word_list = len (cls._word_list)
        
        cls._REFRESH_INTERVAL = refresh
    
    @classmethod
    def dynamicWordFor (cls, static_word):
        _dynamicWord = cls._dynamicWords.get (static_word, None)
        if _dynamicWord is None:
            _dynamicWord = cls (static_word)
            cls._dynamicWords[static_word] = _dynamicWord
        
        return _dynamicWord
    
    def __init__ (self, static_word):
        # https://stackoverflow.com/questions/55102042/why-isnt-the-hash-function-deterministic
        self._secret_salt = abs (int (hashlib.sha256 (static_word.encode ()).hexdigest (), 16)) % (10 ** 8)
        self._random      = random.Random ()
        
        self._last_time   = 0
        self._curr_word   = None
    
    def word (self, interval = 0):
        _curr_time = math.floor ((time.time () + interval * self._REFRESH_INTERVAL) / self._REFRESH_INTERVAL)
        
        if _curr_time != self._last_time:
            self._last_time = _curr_time

            self._random.seed (_curr_time + self._secret_salt)
            _idx            = self._random.randrange (0, self._l_word_list)
            self._curr_word = self._word_list[_idx]
        
        return self._curr_word


def main ():
    DynamicWord.Initialize ('../config/wordlist.txt', 5)

    _static_word  = sys.argv[1] if len (sys.argv) > 1 else "secret"
    _dynamic_word = DynamicWord.dynamicWordFor (_static_word)
    
    for _ in range (0, 15):
        print (list (map (_dynamic_word.word, [-2, -1, 0])))
        time.sleep (6)

if __name__ == "__main__":
    main ()
