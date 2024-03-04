#!/usr/bin/env python3

from enum import Enum, auto
import json
import os
import numbers
from threading import Condition
from threading import Thread    # sliding rate time-out windows
import time

from IsGood import IsGood
from builtins import property


class _AutoName (Enum):
    def _generate_next_value_ (name, _start, _count, last_values):
        return name


class UMState (_AutoName):
    OK              = auto ()
    BAD             = auto ()
    MAX_BYTES       = auto ()
    MAX_ACTION_CNT  = auto ()
    MAX_ACTION_RATE = auto ()
    MAX_ITEM_CNT    = auto ()


class UserModel (IsGood):

    ###################
    # Class variables #
    ###################

    __MAX_BYTES = 'maxBytes'
    __MAX_KB    = 'maxKB'
    __MAX_MB    = 'maxMB'
    __MAX_GB    = 'maxGB'
    __MAX_TB    = 'maxTB'
    __MAX_KIB   = 'maxKiB'
    __MAX_MIB   = 'maxMiB'
    __MAX_GIB   = 'maxGiB'
    __MAX_TIB   = 'maxTiB'

    __MAX_ACTIONS = 'maxActions'
    __MAX_P_ACTS  = 'maxPeriodActions'
    __MAX_ITEMS   = 'maxItems'

    __MAX_BYTES_FACTORS = {
        __MAX_BYTES: 1,
        __MAX_KB:    1000,
        __MAX_MB:    1000 * 1000,
        __MAX_GB:    1000 * 1000 * 1000,
        __MAX_TB:    1000 * 1000 * 1000 * 1000,
        __MAX_KIB:   1024,
        __MAX_MIB:   1024 * 1024,
        __MAX_GIB:   1024 * 1024 * 1024,
        __MAX_TIB:   1024 * 1024 * 1024 * 1024
    }

    __SAVE_PERIOD_SECS  = 'savePeriodSeconds'
    __SAVE_PERIOD_MINS  = 'savePeriodMinutes'
    __SAVE_PERIOD_HOURS = 'savePeriodHours'
    __SAVE_PERIOD_DAYS  = 'savePeriodDays'
    __SAVE_PERIOD_WEEKS = 'savePeriodWeeks'

    __SAVE_PERIOD       = 'savePeriod'

    __SAVE_PERIOD_FACTORS = {
        __SAVE_PERIOD_SECS:  1,
        __SAVE_PERIOD_MINS:  60,
        __SAVE_PERIOD_HOURS: 60 * 60,
        __SAVE_PERIOD_DAYS:  60 * 60 * 24,
        __SAVE_PERIOD_WEEKS: 60 * 60 * 24 * 7
    }

    __SMPL_INTVL_SEC_FCTR  = 'samplingIntervalSeconds'
    __SMPL_INTVL_MIN_FCTR  = 'samplingIntervalMinutes'
    __SMPL_INTVL_HOUR_FCTR = 'samplingIntervalHours'
    __SMPL_INTVL_DAY_FCTR  = 'samplingIntervalDays'

    __SMPL_INTVL_PCT       = 'samplingIntervalPercent'

    __SAMPLING_PERIOD      = 'samplingPeriod'

    __SMPL_INTVL_FACTORS = {
        __SMPL_INTVL_SEC_FCTR:  1,
        __SMPL_INTVL_MIN_FCTR:  60,
        __SMPL_INTVL_HOUR_FCTR: 60 * 60,
        __SMPL_INTVL_DAY_FCTR:  60 * 60 * 24
    }

    ##################
    # Internal class #
    ##################

    class __Sample (object):
        def __init__ (self, nBytes = 0, nItems = 0, _id = None, _type = None):
            super ().__init__ ()

            self.__nBytes = nBytes
            self.__nItems = nItems
            self.__id     = _id
            self.__type   = _type
            self.__time   = time.time ()

        @property
        def numBytes (self):
            return self.__nBytes

        @property
        def numItems (self):
            return self.__nItems

        @property
        def hasCounters (self):
            return self.__nBytes + self.__nItems

        @property
        def id (self):
            return self.__id

        @property
        def type (self):
            return self.__type

        @property
        def time (self):
            return self.__time

    ####################
    # Instance methods #
    ####################

    def __init__ (self, _obj):
        super ().__init__ ()

        self.__condition = Condition ()
        self.__waitCndtn = Condition ()
        self.__states    = set ([UMState.OK])

        if   isinstance (_obj, str):
            if os.path.isfile (_obj):
                try:
                    with open (_obj) as _fIn:
                        _jObj = json.load (_fIn)
                        if isinstance (_jObj, dict):
                            self.__initFromDict (_jObj)
                        else:
                            self.appendErrors (f'JSON file "{_obj}" does not contain a dict')
                except:
                    self.appendErrors (f'Invalid JSON file: "{_obj}"')
            else:
                self.appendErrors (f'Invalid path: "{_obj}"')

        elif isinstance (_obj, dict):
            self.__initFromDict (_obj)

        else:
            self.isGood = (False, f'Bad or missing specification: "{_obj}".')

    def __initFromDict (self, _d):
        self.__samples        = []      # Time-ordered in sample window
        self.__samplesByID    = {}      # Samples indexed by ID within sample window
        self.__oldSamplesByID = {}      # Old samples indexed by ID outside sample window
        self.__trackerThread  = None

        _maxBytes     =  0
        _maxActions   =  0
        _maxPActions  =  0      # maximum number of actions per period
        _maxItems     =  0
        _savePeriod   =  0
        _smplIntvl    =  0
        _smplIntvlPct = 20      # by default, sample the period 5 times

        for _k, _v in _d.items ():
            # Ignore (comment) keys (start with '%')
            if _k.startswith ('%'):
                continue

            if not isinstance (_v, numbers.Number) or _v <= 0:
                self.appendErrors (f'Invalid value "{_v}" for key "{_k}"')
                pass

            elif _k in self.__MAX_BYTES_FACTORS:
                _maxBytes = int (_v * self.__MAX_BYTES_FACTORS[_k])
                setattr (self, self.__MAX_BYTES, _maxBytes)

            elif _k == self.__MAX_ACTIONS:
                _maxActions = int (_v)
                setattr (self, self.__MAX_ACTIONS, _maxActions)

            elif _k == self.__MAX_P_ACTS:
                _maxPActions = int (_v)
                setattr (self, self.__MAX_P_ACTS, _maxPActions)

            elif _k == self.__MAX_ITEMS:
                _maxItems = int (_v)
                setattr (self, self.__MAX_ITEMS, _maxItems)

            elif _k in self.__SAVE_PERIOD_FACTORS:
                _savePeriod = _v * self.__SAVE_PERIOD_FACTORS[_k]

            elif _k in self.__SMPL_INTVL_PCT:
                _smplIntvlPct = _v

            elif _k in self.__SMPL_INTVL_FACTORS:
                _smplIntvl = _v * self.__SMPL_INTVL_FACTORS[_k]

            else:
                self.appendErrors (f'Unknown key/value pair: "{_k}"/"{_v}"')

        if   not _maxActions:
            if _maxPActions:
                _maxActions = _maxPActions
            elif _maxItems:
                _maxActions = _maxItems

            if _maxActions:
                setattr (self, self.__MAX_ACTIONS, _maxActions)

        if _maxActions:
            if not _maxItems:
                _maxItems = _maxActions
                setattr (self, self.__MAX_ITEMS, _maxItems)
    
            if not _maxPActions:
                _maxPActions = _maxActions
                setattr (self, self.__MAX_P_ACTS, _maxPActions)

        self.isGood = (_maxBytes or _maxActions, f'Missing "{self.__MAX_BYTES}", "{self.__MAX_ACTIONS}", or "{self.__MAX_ITEMS}"')

        if self.isGood and _savePeriod:
            setattr (self, self.__SAVE_PERIOD, _savePeriod)
            self.__initSampler (_smplIntvl if _smplIntvl else _savePeriod * _smplIntvlPct / 100)

        if self.isGood:
            self.numBytes   = 0
            self.numActions = 0
            self.numItems   = 0
        else:
            self.__addState (UMState.BAD, False)

    def __initSampler (self, _vFloat):
        setattr (self, self.__SAMPLING_PERIOD, _vFloat)

    @property
    def counters (self):
        with self.condition:
            return self.numActions, self.numItems, self.numBytes

    @property
    def trackerCounters (self):         # returns (number of samples in period, number of old samples with IDs)
        with self.condition:
            return len (self.__samples), len (self.__oldSamplesByID)

    @property
    def isGood (self):
        return super ().isGood and self.hasState (UMState.OK)

    # Without the following, Python 3.7 fails with "AttributeError: can't set attribute"
    # (see https://gist.github.com/Susensio/979259559e2bebcd0273f1a95d7c1e79):

    @isGood.setter
    def isGood (self, _obj):
        super (UserModel, type (self)).isGood.fset (self, _obj)

    @property
    def condition (self):
        return self.__condition

    @property
    def states (self):
        return set (self.__states)

    def hasState (self, _state):
        return _state in self.__states

    def onlyHasState (self, _state):
        return len (self.__states) == 1 and self.hasState (_state)

    def __addState (self, _state, notify = True):   # MUST BE called within 'with self.condition' context!
        if not self.hasState (_state):
            self.__states.add (_state)

            if _state != UMState.OK:
                self.__states.discard (UMState.OK)

            if notify:
                self.condition.notify ()

    def __removeState (self, _state):       # MUST BE called within 'with self.condition' context!
        if self.hasState (_state):
            self.__states.discard (_state)

            if len (self.__states) == 0:
                self.__addState (UMState.OK, False)

            self.condition.notify ()

    def __appendSample (self, sample, samples, samplesByID):    # MUST BE called within 'with self.condition' context!
        if samples is not None:
            samples.append (sample)
        if sample.id:
            samplesByID[sample.id] = sample

    def __findSample (self, _id):           # MUST BE called within 'with self.condition' context!
        for _sDict, _samples in ((self.__samplesByID, self.__samples), (self.__oldSamplesByID, None)):
            if _id in _sDict:
                return _sDict.get (_id), _sDict, _samples

        return None, None, None

    def __removeSample (self, _id):         # MUST BE called within 'with self.condition' context!
        _sample, _sDict, _samples = self.__findSample (_id)

        if _sample:
            if _samples:
                _samples.remove (_sample)
            del _sDict[_id]

        return _sample

    def __makeTracker (self):
        
        def periodTracker ():
            _savePeriod     = getattr (self, self.__SAVE_PERIOD)
            _samplingPeriod = getattr (self, self.__SAMPLING_PERIOD)
            _maxPActions    = getattr (self, self.__MAX_P_ACTS)
            
            while True:
                with self.condition:

                    # Provisionally age out entries

                    _currTime = time.time ()

                    while self.__samples:
                        _sample = self.__samples[0]

                        # The sample aged out

                        if _sample.time + _savePeriod < _currTime:
                            _ = self.__removeSample (_sample.id) if _sample.id in self.__samplesByID else self.__samples.pop (0)

                            # Track only old samples with IDs and counters (for trackRemove ())

                            if _sample.hasCounters and _sample.id:
                                self.__appendSample (_sample, None, self.__oldSamplesByID)

                        # The first sample is within the sampling period

                        else:
                            break

                    # We're below the maximum submission rate

                    if   len (self.__samples) <  _maxPActions:
                        self.__removeState (UMState.MAX_ACTION_RATE)

                    # We've exceeded the maximum submission rate

                    elif len (self.__samples) >= _maxPActions:
                        self.__addState (UMState.MAX_ACTION_RATE)

                with self.__waitCndtn:
                    self.__waitCndtn.wait (_samplingPeriod)    # wait for the next sampling period or notification

        # Provisionally start the sampling thread

        if hasattr (self, self.__SAVE_PERIOD) and hasattr (self, self.__MAX_ACTIONS):
            if self.__trackerThread is None:
                self.__trackerThread = Thread (target = periodTracker, args = (), daemon = True)
                self.__trackerThread.start ()
            else:
                self.__notifyTracker ()

    def __notifyTracker (self):
        if self.__trackerThread:
            with self.__waitCndtn:
                self.__waitCndtn.notify ()          # Pre-emptively notify tracker that a sample has been added

    def trackAdd (self, nBytes = 0, nItems = 1, _id = None, _type = 'data'):
        if self.isGood:
            with self.condition:

                # Track action limit

                _hasMaxActions = hasattr (self, self.__MAX_ACTIONS)
                if _hasMaxActions:
                    self.numActions += 1
                    if self.numActions > getattr (self, self.__MAX_ACTIONS):
                        self.__addState (UMState.MAX_ACTION_CNT)

                # Track item limit

                _hasMaxItems = hasattr (self, self.__MAX_ITEMS)
                if _hasMaxItems:
                    self.numItems += nItems
                    if self.numItems > getattr (self, self.__MAX_ITEMS):
                        self.__addState (UMState.MAX_ITEM_CNT)

                # Track byte submission limit

                _hasMaxBytes = hasattr (self, self.__MAX_BYTES)
                if nBytes and _hasMaxBytes:
                    self.numBytes += nBytes
                    if self.numBytes > getattr (self, self.__MAX_BYTES):
                        self.__addState (UMState.MAX_BYTES)

                # Track sample

                if _hasMaxActions or _hasMaxItems or _hasMaxBytes:
                    self.__appendSample (self.__Sample (nBytes, nItems, _id, _type), self.__samples, self.__samplesByID)

                    # Track rate window history

                    if hasattr (self, self.__SAVE_PERIOD):
                        self.__makeTracker ()

    def trackRemove (self, nBytes = 0, nItems = 1, _id = None, _type = 'data'):
        if not (self.hasState (UMState.MAX_ACTION_CNT) or self.hasState (UMState.MAX_ACTION_RATE)):
            with self.condition:

                _sample = self.__removeSample (_id)     # obtain nBytes and nItems from _id if known
                if _sample:
                    nBytes = _sample.numBytes
                    nItems = _sample.numItems

                # Track item limit

                _hasMaxItems = hasattr (self, self.__MAX_ITEMS)
                if _hasMaxItems:
                    if self.numItems >= nItems:
                        self.numItems -= nItems
                        if self.hasState (UMState.MAX_ITEM_CNT) and self.numItems < getattr (self, self.__MAX_ITEMS):
                            self.__removeState (UMState.MAX_ITEM_CNT)

                # Track byte submission limit

                _hasMaxBytes = hasattr (self, self.__MAX_BYTES)
                if nBytes and _hasMaxBytes:
                    if self.numBytes >= nBytes:
                        self.numBytes -= nBytes
                        if self.hasState (UMState.MAX_BYTES) and self.numBytes < getattr (self, self.__MAX_BYTES):
                            self.__removeState (UMState.MAX_BYTES)

                # Append removal action

                self.__appendSample (self.__Sample (), self.__samples, self.__samplesByID)

                # Remove the sample

                _ = self.__removeSample (_id)

                self.__notifyTracker ()

########
# main #
########

def main ():
    _umDict = {}

    _userModels = {}

    for _svr, _sDict in _umDict.items ():
        _userModels[_svr] = UserModel (_sDict)

    for _svr, _um in _userModels.items ():
        print (f'"{_svr}":\t{vars (_um)}')


if __name__ == "__main__":
    main ()
