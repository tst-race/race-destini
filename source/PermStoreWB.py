import inspect
import os
import random
import re
import sys
from threading import Condition, RLock
import time

from AbsWhiteboard import AbsWhiteboard
from DiagPrint import diagPrint
from DynamicTags import DynamicTags

# https://stackoverflow.com/questions/8777753/converting-datetime-date-to-utc-timestamp-in-python

from datetime import datetime, timezone, timedelta

_dt_utc  = datetime (1970, 1, 1, tzinfo = timezone.utc)
_t_del_1 = timedelta (seconds = 1)


def _datetime_to_posix (_dt):
    return (_dt - _dt_utc) / _t_del_1


class _SharedCache (object):

    _MIN_HIGH  = 4

    _singleton = None

    def __init__ (self, high):
        assert self.__class__._singleton is None, 'ERROR: only one instance may be created'

        self.__class__._singleton = self

        assert high > self._MIN_HIGH, 'ERROR: "high" is too small'

        super ().__init__ ()

        self._lock  = RLock ()
        self._curr  = set ()        # if len (_curr) reaches self._high,
        self._cache = set ()        # copy _curr to _cache; reset _curr to empty.
        self._high  = high          # len of _curr to trigger _curr -> _cache

    @classmethod
    def getSingleton (cls, high = 10000):
        if not cls._singleton:
            cls._singleton = cls (high)

        return cls._singleton

    def isCached (self, obj):
        with self._lock:
            _isCached = obj in self._cache

        return _isCached

    def cache (self, obj):
        with self._lock:
            _isCached = obj in self._cache

            if not _isCached:
                self._cache.add (obj)

            self._curr.add (obj)

        return _isCached

    def checkCache (self):
        with self._lock:

            # Set _cache to _curr if the latter has more than _high elts

            if len (self._curr) > self._high:
                self._cache = self._curr
                self._curr  = set ()

class Whiteboard (AbsWhiteboard):

    _DEFAULT_MIN_NUM_TAGS = 3
    _DEFAULT_MAX_NUM_TAGS = 7

    _PERM_STORE_EXT = 'perm'

    @staticmethod
    def _listfromdict (_dict, _key):
        _list = _dict.get (_key, None)
        return _list if isinstance (_list, list) else None

    def __init__ (self, user, credentials, userContext, wbInstance, wbCConfig):

        # Prevent direct instantiation of this class

        _type = type (self)
        #_type = None

        if _type == __class__:
            raise NotImplementedError ('{} may not be instantiated'.format (_type))

        # Initialization

        self.wbClass = wbInstance.get ('class', None)
        diagPrint (f'{self.wbClass} Whiteboard.__init__ ({user}, {credentials}, {userContext}, {wbInstance}, {wbCConfig})')

        super ().__init__ (user, credentials, userContext, wbInstance, wbCConfig)

        self.user       = user
        self.wbInstance = wbInstance

        self.min_num_tags = wbCConfig.get ('min_num_tags', self._DEFAULT_MIN_NUM_TAGS)
        self.max_num_tags = wbCConfig.get ('max_num_tags', self._DEFAULT_MAX_NUM_TAGS)

        # Validate that the user context contains tags and its required entries.

        tags   = userContext.get ('tags', None)
        isgood = isinstance (tags, dict)

        if isgood:
            self.dynTagsBrdcst = []

            _tagList = self._listfromdict (tags, 'broadcast')

            if _tagList:
                for _tag in _tagList:
                    self.dynTagsBrdcst.append (DynamicTags.dynamicTagsFor (_tag, self.min_num_tags, self.max_num_tags))

            _tagList = self._listfromdict (tags, 'pulling')

            if _tagList:
                self.dynTagsPulling = DynamicTags.dynamicTagsFor (_tagList[0],
                                                                  self.min_num_tags, self.max_num_tags)
            else:
                self.dynTagsPulling = None

            isgood = self.dynTagsBrdcst or self.dynTagsPulling

        if not isgood:
            raise KeyError ('Missing "tags" or subkeys')

        self.recvThread = None
        self.recvLock   = Condition ()
        self.recvQueue  = []
        self.fileCache  = _SharedCache.getSingleton ()

        self.perm_path  = None


    # Use credentials, wbInstance, and wbCConfig maps to open and return a channel.
    #
    # user           # 'Bob Evans'
    # userContext    # {'tags': {'broadcast': ['#brdcastAnon', '#brdcast127'],
    #                            'pushing': ['#monument', '#senate'],
    #                            'pulling': ['#scotus', '#omb']
    #                           }
    # wbInstance     # {'class': 'PermStoreWB'}
    # wbCConfig      # {'perm_path': <dir>,
    #                   'connection_duration': 600,
    #                   'initial_retry_wait': 4,
    #                   'max_retry_count': 5,
    #                   'next_wait_lambda': 'lambda _t: 2 * _t # exponential backoff'}

    def openChannel (self, user, _credentials, _userContext, _wbInstance, wbCConfig):

        self.perm_path = wbCConfig.get ('perm_path', '/tmp')

        diagPrint (f'>>> {self.wbClass} openChannel: {wbCConfig}, {self.perm_path}')

        return True     # subclass must implement and return channel object

    # Close the channel

    def closeChannel (self, channel):
        pass

    # Wait for and return inbound message

    def recvMsg (self, userContext):

        # Employ recMsg queue

        if self.recvThread is None:
            _t_name = f'{self.wbClass}-recvMsg-{self.user}'
            self.recvThread = self.startThread (_t_name, self._recvMsg, (userContext, ))
            diagPrint (f'+++ Starting thread "{_t_name}"')

        while self._channel:    # accommodate the channel being asynchronously closed
            with self.recvLock:
                if self.recvQueue:
                    _msgIn = self.recvQueue.pop (0)

                    diagPrint (f'popping 1... input: {len (_msgIn)}')

                    return _msgIn
                else:
                    self.recvLock.wait ()

        return None

    def getMaxSendMsgCount (self):
        return 1

    # Send a message.  Return True if successful, False if retry.

    def sendMsg (self, destContext, msgList):

        # Per https://stackoverflow.com/questions/5067604/determine-function-name-from-within-that-function-without-using-traceback
        _moduleName     = os.path.basename (__file__).split ('.')[0]
        _methodNameBare = f'{_moduleName}.{__class__.__qualname__}.{inspect.stack ()[0][3]}'

        diagPrint (f'{_methodNameBare} ({destContext}, {len (msgList)})')

        if not msgList:
            return False

        _, userContext = destContext
        wb_tags = userContext.get ('tags')

        _pulling = wb_tags.get ('pulling', None)

        diagPrint (f"User Context Pulling is {_pulling}")

        if _pulling:
            _pTags = list (_pulling)
        else:
            _pTags = list (wb_tags.get ('broadcast'))

        # Append time-based dynamic tag

        for msg in msgList:
            _dynTags  = DynamicTags.dynamicTagsFor (_pTags[0], self.min_num_tags, self.max_num_tags)
            tag       = _dynTags.tags ()[0]

            diagPrint (f'sendMsg () with tag {tag}')
            _dt_posix = _datetime_to_posix (datetime.now (timezone.utc))
            _msgOut   = os.path.join (self.perm_path, f'{_dt_posix}-{tag}.{self._PERM_STORE_EXT}')

            with open (_msgOut, 'wb') as _fOut:
                _fOut.write (msg)

        return True    # return status

    def _recvMsg (self, _userContext):

        loop_delay = self.wbInstance.get ('loop_delay', 1)
        lfn_cache  = set ()

        # Poll for forever

        while True:

            # Search last three tag intervals, starting with "now".

            bDynTags = []
            for _dynTagBrdcst in self.dynTagsBrdcst:
                bDynTags.extend (list (map (_dynTagBrdcst.tags, [0, -1, -2])))
            pDynTags = list (map (self.dynTagsPulling.tags, [0, -1, -2]))

            dynTags = bDynTags
            dynTags.extend (pDynTags)

            for search_tags in dynTags:
                # Search for time-based dynamic word
                search_tag = search_tags[random.randrange (len (search_tags))]
                search_re  = re.compile (r'[0-9.]+-' + f'{search_tag}.{self._PERM_STORE_EXT}')

                while True:         # "do once" loop that permits early exits
                    try:
                        messages = []
                        for dirpath, _, filenames in os.walk (self.perm_path):
                            for _file in filenames:
                                if search_re.match (_file):
                                    if _file in lfn_cache:
                                        continue

                                    lfn_cache.add (_file)
                                    diagPrint (f"{self.wbClass}._recvMsg () appending {_file}")
                                    messages.append (os.path.join (dirpath, _file))
                            break
                    except Exception as e:
                        self.incrementStatus ('searchError')
                        diagPrint (f"Exception error 2: {sys.exc_info ()[0]} {e}")
                        break               # TBD: is this a pathological failure?

                    self.fileCache.checkCache ()

                    for message in messages:
                        if self.fileCache.isCached (message):
                            continue

                        try:
                            with self.recvLock:
                                diagPrint (f"{self.wbClass}._recvMsg () reading {message}")
                                with open (message, 'rb') as _fIn:
                                    msgContent = _fIn.read ()

                                self.fileCache.cache (message)
                                self.recvQueue.append (msgContent)
                                self.recvLock.notify ()
                        except:
                            self.incrementStatus ('getMessageError')
                            diagPrint (f"Exception error 3: message fetch failed; {sys.exc_info ()[0]}")

                    break           # "do once"

            # Sleep before next crawl; the duration is specified in the JSON

            time.sleep (2 * loop_delay)
