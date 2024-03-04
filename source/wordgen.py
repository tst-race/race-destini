#!/usr/bin/env python
import os
import sys
import glob
import time
# import pywedge
import datetime
from DynamicTags import *

default_cover_dir = "/opt/projects/RACE/images/inria-jpeg1/"

SLEEP_TIME = 1

class WordGen:
    def __init__(self, secret='secret', sender=True):
        self.min_num_tags = 1
        self.max_num_tags = 1
        self.dt = DynamicTags.dynamicTagsFor (secret, self.min_num_tags, self.max_num_tags)
        if sender:
            self.nwords = 1
        else:
            self.nwords = 3

    def get_word(self):
        if self.nwords == 1:  # Sender side will ask for one word
            result = self.dt.words(num_words=1)
            return result
        elif self.nwords == 3:
            presult = set( sum( list( map(self.dt.words, [0, -1, -2]) ) ) )
            result = presult.union(presult)
        return result
    



def main ():
    DynamicTags.Initialize ('../config/wordlist.txt', 5)

    wg = WordGen(sender=True)
    
    for _ in range (0, 15):
        print(wg.get_word())
        time.sleep (6)

if __name__ == "__main__":
    main ()
