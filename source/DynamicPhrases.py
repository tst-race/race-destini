#!/usr/bin/env python

import math
import random
import sys
import time




class DynamicPhrases:

    _phraseList = None
    _listLen = 0

    @classmethod
    def Initialize (cls, phraseFile):
        with open (phraseFile) as _f:
            cls._phraseList   = _f.read ().splitlines ()
            cls._listLen = len(cls._phraseList)
    
    @classmethod
    def getRandomPhrase (cls):
        return cls._phraseList[random.randrange(cls._listLen)]


def main ():
    DynamicPhrases.Initialize ('phrases.txt')
    print (DynamicPhrases.getRandomPhrase())
    print (DynamicPhrases.getRandomPhrase())
    print (DynamicPhrases.getRandomPhrase())    


if __name__ == "__main__":
    main ()
