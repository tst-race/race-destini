#!/usr/bin/env python

import sys
import json
import time
import random
import os.path



def load_param_file(filename="./wbparams.json", verbose=False):
    if not os.path.exists(filename):
        return {}
    sl = []
    with open(filename) as f:
        for raw in f:
            l = raw.split('//')[0][0:-1]
            if len(l) > 0:
                sl = sl + [ l ]
                if verbose:
                    print(l)
    json_in = ' '.join(sl)
    desc = json.loads(json_in)
    return desc

def make_waiter_from_params_dict(d):
    w = burstyWaiter(limit=d['limit'],
                     interval=d['interval'],
                     burst_limit=d['burst_limit'],
                     burst_interval=d['burst_interval'])
    return w

def make_waiter_set(desc):
    waiters = {}
    for key in desc:
        dtop = desc[key]
        pw = make_waiter_from_params_dict(dtop['postLimits'])
        qw = make_waiter_from_params_dict(dtop['queryLimits'])

        waiters[key] = [ pw, qw ]
    return waiters

#
# ImgChat has a primitive 'sleep' function that randomly waits.  For
# 'auto' mode, we need to beef this up.  Implement a class that has a
# poisson-ish model for random wait-and-retry.
#
# The object should represent a daily limit and a "used-so-far" count.
#

# This class just waits randomly with no batching:  

class simpleWaiter:
    def __init__(self, limit=250, interval=250, min_wait=0.2, periodic=True):
        self.set_params(limit, interval, min_wait, periodic)

    def set_params(self, limit, interval, min_wait, periodic=True):
        #print(f"simpleWaiter setting parameters: limit={limit}, interval={interval} seconds, min wait={min_wait} seconds.")
        self.periodic = periodic
        self.limit = limit
        self.interval = interval
        self.min_wait = min_wait
        self.t1 = time.time()
        self.reset()


    # ==  Class simpleWaiter  ==
    # Return True if we have hit the limit:
    def is_at_limit(self):
        return self.used_so_far >= self.limit
        
    # The interval represents some definite clock boundary in local
    # time, e.g. "midnight", so we need to do some integer arithmetic.
    # The computations are performed with millisecond precision, to
    # allow more precision in the interval and min_wait parameters:
    # ==  Class simpleWaiter  ==
    def reset(self):
        self.t0 = self.t1
        next = int( self.t0 / self.interval ) 
        self.t1 = (next + 1) * self.interval
        self.used_so_far = 0    # Number of calls made so far in this interval

    # Model for simpleWaiter: Let remaining = limit - used_so_far.
    # Compute dt = interval / remaining = seconds per action.  Pick a
    # random number of seconds in the interval [1,dt] and sleep for that
    # time.  Increment used_so_far.

    # ==  Class simpleWaiter  ==
    def compute_wait(self):
        remaining = self.limit - self.used_so_far
        if remaining <= 0:
            remaining = 1
        dt = float(self.interval) / float(remaining)
        if dt < self.min_wait:
            # The waiter has a minimum (perhaps an API limitation, or
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

    # ==  Class simpleWaiter  ==
    def wait(self):
        remaining = self.limit - self.used_so_far
        if remaining <= 0:
            remaining = 1
        dt = float(self.interval) / float(remaining)
        if dt < self.min_wait:
            # The waiter has a minimum (perhaps an API limitation, or
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
        # Waiters can be periodic or non-periodic.  In the periodic
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
# Bursty waiter uses simpleWaiter's long-term dynamics, but when
# simpleWaiter says go, this one kicks down to a separate simpleWaiter
# that handles the burst.

class burstyWaiter(simpleWaiter):
    _BURST = 1
    _LONG = 2
    
    def __init__(self, limit=250, interval=250, min_wait=0.1, periodic=True, burst_limit=10, burst_interval=2):
        super().__init__(limit, interval, min_wait, periodic)
        self.mode = self._LONG
        self.burst_limit = burst_limit
        self.burst_interval = burst_interval
        self.burst_waiter = simpleWaiter(burst_limit, burst_interval, periodic=False)
        self.randomize_burst_params()

    def randomize_burst_params(self):
        limit = random.randrange(1,self.burst_limit)
        interval = random.randrange(1,self.burst_interval)
        self.burst_waiter.limit = limit
        self.burst_waiter.interval = interval
        self.burst_waiter.reset()
        
    # Need to think about this.  Two modes: short and long.  In long
    # mode, wait, but upon waking, flip to short mode and return.  In
    # short mode, use bursting until the random burst limit is reached.
    def wait(self):
        if self.mode == self._LONG:
            super().wait()
            self.mode = self._BURST
            print("> burst", end="")
            sys.stdout.flush()
        else:
            self.burst_waiter.wait()
            self.used_so_far += 1
            print('.', end="")
            sys.stdout.flush()
            if self.burst_waiter.is_at_limit():
                self.mode = self._LONG
                print("> long")
                self.randomize_burst_params()


# Model for batchWaiter: pick a number in [1,batch].  This is a short batch of
# posts or queries.  This number is added to used_so_far to
# keep track of calls.  Now randomly wait "long enough" before
# trying again.  This model should be used for send and
# receive.



def main ():
    if len(sys.argv) != 3:
        print("Usage:  waiter.py <limit> <interval>")
        quit()
        
    limit = int(sys.argv[1])
    interval = int(sys.argv[2])
    
    # waiter = simpleWaiter(limit, interval, 0.1)
    waiter = burstyWaiter(limit, interval, 0.1)

    while True:
        print(f"simpleWaiter: {waiter.used_so_far}")
        waiter.wait()

if __name__ == "__main__":
    main ()
