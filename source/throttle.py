#!/usr/bin/env python

import sys
import json
import time
import random
import os.path

# Define a "throttle" class hierarchy that creates the appearance of
# random, human-like interaction with whiteboards.  Throttles help us
# avoid violation of resource limitations imposed by the whiteboards:

def make_throttle_from_params_dict(d):
    w = BurstyThrottle(limit=d['limit'],
                     interval=d['interval'],
                     burst_limit=d['burst_limit'],
                     burst_interval=d['burst_interval'])
    return w

def make_throttle_set(desc):
    throttles = {}
    for key in desc:
        dtop = desc[key]
        pw = make_throttle_from_params_dict(dtop['postLimits'])
        qw = make_throttle_from_params_dict(dtop['queryLimits'])

        throttles[key] = [ pw, qw ]
    return throttles

# Implement a class that has a poisson-ish model for random
# wait-and-retry.
#
# The object should represent a daily limit and a "used-so-far" count.
#

# This class just waits randomly with no batching:  

class SimpleThrottle:
    def __init__(self, limit=250, interval=250, min_wait=0.2, periodic=True):
        self.set_params(limit, interval, min_wait, periodic)

    def set_params(self, limit, interval, min_wait, periodic=True):
        #print(f"SimpleThrottle setting parameters: limit={limit}, interval={interval} seconds, min wait={min_wait} seconds.")
        self.periodic = periodic
        self.limit = limit
        self.interval = interval
        self.min_wait = min_wait
        self.t1 = time.time()
        self.reset()


    # ==  Class SimpleThrottle  ==
    # Return True if we have hit the limit:
    def is_at_limit(self):
        return self.used_so_far >= self.limit
        
    # The interval represents some definite clock boundary in local
    # time, e.g. "midnight", so we need to do some integer arithmetic.
    # The computations are performed with millisecond precision, to
    # allow more precision in the interval and min_wait parameters:
    # ==  Class SimpleThrottle  ==
    def reset(self):
        self.t0 = self.t1
        next = int( self.t0 / self.interval ) 
        self.t1 = (next + 1) * self.interval
        self.used_so_far = 0    # Number of calls made so far in this interval

    # Model for SimpleThrottle: Let remaining = limit - used_so_far.
    # Compute dt = interval / remaining = seconds per action.  Pick a
    # random number of seconds in the interval [1,dt] and sleep for that
    # time.  Increment used_so_far.

    # ==  Class SimpleThrottle  ==
    def compute_wait(self):
        remaining = self.limit - self.used_so_far
        if remaining <= 0:
            remaining = 1
        dt = float(self.interval) / float(remaining)
        if dt < self.min_wait:
            # The throttle has a minimum (perhaps an API limitation, or
            # to capture inescapable overhead):
            seconds = self.min_wait
        else:
            # We bump up the precision to get a random interval in
            # milliseconds:
            lo = int(1000.0 * self.min_wait)
            hi = int(1000.0 * dt)
            if hi <= lo:
                milliseconds = lo
            else:
                milliseconds = random.randrange(lo, hi)
            # Then bump down to get a float in seconds at ms resolution:
            seconds = milliseconds / 1000.0
        return seconds

    # ==  Class SimpleThrottle  ==
    def wait(self):
        remaining = self.limit - self.used_so_far
        if remaining <= 0:
            remaining = 1
        dt = float(self.interval) / float(remaining)
        if dt < self.min_wait:
            # The throttle has a minimum (perhaps an API limitation, or
            # to capture inescapable overhead):
            seconds = self.min_wait
        else:
            # We bump up the precision to get a random interval in
            # milliseconds:
            lo = int(1000.0 * self.min_wait)
            hi = int(1000.0 * dt)
            if hi <= lo:
                milliseconds = lo
            else:
                milliseconds = random.randrange(lo, hi)
            # Then bump down to get a float in seconds at ms resolution:
            seconds = milliseconds / 1000.0
        # Sleep we must:
        time.sleep(seconds)

        # We have used up one call:
        self.used_so_far += 1
        
        # What time is it now?
        tcur = int(time.time())
        # Throttles can be periodic or non-periodic.  In the periodic
        # case, if current time is past the computed interval, then
        # reset.  In non-periodic mode, it's up to the caller to
        # reset:
        if self.periodic and tcur > self.t1:
            self.reset()
        else:
            # If this is true then we have exhausted our allocation.
            # Wait until the interval has passed:
            if self.is_at_limit():
                if self.t1 > tcur:
                    time.sleep(self.t1 - tcur)

            tcur = int(time.time())
            # Again, only do the reset if we are periodic:
            if self.periodic and tcur > self.t1:
                # If we passed the interval, then reset everything:
                self.reset()



#
# Bursty throttle uses SimpleThrottle's long-term dynamics, but when
# SimpleThrottle says go, this one kicks down to a separate SimpleThrottle
# that handles the burst.

class BurstyThrottle(SimpleThrottle):
    _BURST = 1
    _LONG = 2
    
    def __init__(self, limit=250, interval=250, min_wait=0.1, periodic=True, burst_limit=10, burst_interval=2):
        super().__init__(limit, interval, min_wait, periodic)
        self.mode = self._LONG
        self.burst_limit = burst_limit
        self.burst_interval = burst_interval
        self.burst_throttle = SimpleThrottle(burst_limit, burst_interval, periodic=False)
        self.randomize_burst_params()

    def randomize_burst_params(self):
        limit = random.randrange(1,self.burst_limit)
        interval = random.randrange(1,self.burst_interval)
        self.burst_throttle.limit = limit
        self.burst_throttle.interval = interval
        self.burst_throttle.reset()
        
    # Need to think about this.  Two modes: short and long.  In long
    # mode, wait, but upon waking, flip to short mode and return.  In
    # short mode, use bursting until the random burst limit is reached.
    def wait(self):
        if self.mode == self._LONG:
            super().wait()
            self.mode = self._BURST
            #print("> burst", end="")
            #sys.stdout.flush()
        else:
            self.burst_throttle.wait()
            self.used_so_far += 1
            #print('.', end="")
            #sys.stdout.flush()
            if self.burst_throttle.is_at_limit():
                self.mode = self._LONG
                #print("> long")
                self.randomize_burst_params()


# Model for batchThrottle: pick a number in [1,batch].  This is a short batch of
# posts or queries.  This number is added to used_so_far to
# keep track of calls.  Now randomly wait "long enough" before
# trying again.  This model should be used for send and
# receive.



def main ():
    if len(sys.argv) != 3:
        print("Usage:  throttle.py <limit> <interval>")
        quit()
        
    limit = int(sys.argv[1])
    interval = int(sys.argv[2])
    
    # throttle = SimpleThrottle(limit, interval, 0.1)
    throttle = BurstyThrottle(limit, interval, 0.1)

    while True:
        print(f"SimpleThrottle: {throttle.used_so_far}")
        throttle.wait()

if __name__ == "__main__":
    main ()
