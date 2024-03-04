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

class DynamicWords (object):
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
    def dynamicWordsFor (cls, static_word, min_num_words = 1, max_num_words = 1):
        _dynamicWords = cls._dynamicWords.get (static_word, None)
        if _dynamicWords is None:
            _dynamicWords = cls (static_word, min_num_words, max_num_words)
            cls._dynamicWords[static_word] = _dynamicWords
        
        return _dynamicWords
    
    def __init__ (self, static_word, min_num_words, max_num_words):
        if min_num_words < 1:
            min_num_words = 1
        if max_num_words < min_num_words:
            max_num_words = min_num_words

        # https://stackoverflow.com/questions/55102042/why-isnt-the-hash-function-deterministic
        self._secret_salt   = abs (int (hashlib.sha256 (static_word.encode ()).hexdigest (), 16)) % (10 ** 8)
        self._random        = random.Random ()
        self._min_num_words = min_num_words
        self._max_num_words = max_num_words
    
    def words (self, interval = 0):
        _curr_time = math.floor ((time.time () + interval * self._REFRESH_INTERVAL) / self._REFRESH_INTERVAL)
        _word_list = []

        self._random.seed (_curr_time + self._secret_salt)

        _num_words = self._random.randrange (self._min_num_words, self._max_num_words + 1)
        for _ in range (_num_words):
            _idx = self._random.randrange (0, self._l_word_list)
            _word_list.append (self._word_list[_idx])
        
        return _word_list


def main ():
    DynamicWords.Initialize ('../config/wordlist.txt', 5)

    _static_word   = sys.argv[1] if len (sys.argv) > 1 else "secret"
    _dynamic_words = DynamicWords.dynamicWordsFor (_static_word, 3, 5)
    
    for _ in range (0, 15):
        print (list (map (_dynamic_words.words, [-2, -1, 0])))
        time.sleep (6)

if __name__ == "__main__":
    main ()
