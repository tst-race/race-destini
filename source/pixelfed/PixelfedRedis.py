import base64
import io
import os
import random
import subprocess
import sys
import tempfile
import hashlib
from threading import Thread, Condition, RLock
import time
#from essential_generators import DocumentGenerator
from urllib.parse import quote

import requests
from urllib3.exceptions import InsecureRequestWarning


from AbsWhiteboard import AbsWhiteboard
from DiagPrint import diagPrint
from DynamicTags import DynamicTags


# max sleep interval for explicit wait calls
max_sleep = 15



class _SharedCache_Pix (object):

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

    _PusherDriver = None
    _PusherClosed = False
    _PusherMutex  = RLock ()
    wb_hostname = ""

    

    @staticmethod
    def _listfromdict (_dict, _key):
        _list = _dict.get (_key, None)
        return _list if isinstance (_list, list) else None

    def __init__ (self, user, credentials, tags, wbInstance, wbCConfig):

        # Prevent direct instantiation of this class

        _type = type (self)
        #_type = None

        if _type == __class__:
            raise NotImplementedError ('{} may not be instantiated'.format (_type))

        # Initialization

        super ().__init__ (user, credentials, tags, wbInstance, wbCConfig)

        self.user       = user
        self.wbInstance = wbInstance
        self.inactive_count = 0
        self.wb_hostname = wbInstance.get('url', None)

        if self.wb_hostname:
            self.wb_hostname = self.wb_hostname.replace('https', 'http')


        self.min_num_tags   = wbCConfig.get ('min_num_tags', self._DEFAULT_MIN_NUM_TAGS)
        self.max_num_tags   = wbCConfig.get ('max_num_tags', self._DEFAULT_MAX_NUM_TAGS)

        self.dynTagsBrdcst  = []
        self.dynTagsPulling = None
        #self.doc_gen = DocumentGenerator()

        diagPrint(f"Pixelfed: Tags: {tags}")

        if isinstance (tags, dict):
            _tagList = self._listfromdict (tags, 'broadcast')
            
            if _tagList:
                for _tag in _tagList:
                    self.dynTagsBrdcst.append (DynamicTags.dynamicTagsFor (_tag, self.min_num_tags, self.max_num_tags))

            _tag = tags.get ('pulling', None)

            diagPrint(f"Pixelfed: Tags2: {_tag}")
            
            if isinstance (_tag, str):
                self.dynTagsPulling = DynamicTags.dynamicTagsFor (_tag,
                                                                  self.min_num_tags, self.max_num_tags)
        elif isinstance (tags, str):
            diagPrint(f"Pixelfed: Tags3: {tags}")
            self.dynTagsPulling = DynamicTags.dynamicTagsFor (tags,
                                                              self.min_num_tags, self.max_num_tags)

        isgood = self.dynTagsBrdcst or self.dynTagsPulling

        if not isgood:
            raise KeyError ('Missing "tags" or subkeys')

        self.recvThread = None
        self.recvLock   = Condition ()
        self.recvQueue  = []
        self.recvMutex  = Condition ()
 
        self._url_cache = _SharedCache_Pix.getSingleton ()

        if 'ANDROID_BOOTLOGO' in os.environ:
            os.system('/system/bin/chmod 755 /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/scripts/*')
            os.system('/system/bin/chmod 755 /data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/bin/*')

    def openChannel (self, user, credentials, _unused, wbInstance, wbCConfig):
        return True
        

    # Close the channel

    def closeChannel (self, channel):
        self._channel = None
        

    # Wait for and return inbound message 

    def recvMsg (self, userContext):

        # Employ recMsg queue; run selenium poller in thread

        if self.recvThread is None:
            _t_name = 'Pixelfed-recvMsg-{}'.format (self.user)
            self.recvThread = self.startThread (_t_name, self._recvMsg, (userContext, ))

        while self._channel:    # accommodate the channel being asynchronously closed
            with self.recvLock:
                if self.recvQueue:
                    _imgIn = self.recvQueue.pop (0)

                    diagPrint (f'popping 1... input: {len (_imgIn)}')
                    return _imgIn                   
                else:
                    self.recvLock.wait ()

        return None

    def _recvMsg (self, userContext):
        try:
            self._recvMsgPriv (userContext)
        except Exception as e:
            diagPrint (f"Error in recvMsgPriv {e}" )
            

    def _recvMsgPriv (self, userContext):
        loop_delay = self.wbInstance.get ('loop_delay', 1)
        prev_count = 0

        # key:category, value:last index 
        cat_indices = {}

        diagPrint("In _recvMsg_")


        # Poll for forever or until the channel is closed

        while True: 
            diagPrint (f"looping inside PixelfedRedis:_recvMsgPriv")

            # Search last three tag intervals, starting with "now".
            bDynTags = []
            for _dynTagBrdcst in self.dynTagsBrdcst:
                bDynTags.extend (list (map (_dynTagBrdcst.words, [0, -1])))
            pDynTags = list (map (self.dynTagsPulling.words, [0, -1]))

            dynTags = bDynTags
            dynTags.extend (pDynTags)
            self.inactive_count = self.inactive_count + 1

            for search_tags in dynTags:
                # Search for time-based dynamic word (viz., tag without leading '#')
                # Note: we're not using tags in 'common'

                while True:         # "do once" loop that permits early exits
                    search_tag      = search_tags[random.randrange (len (search_tags))]
                    diagPrint (f"Pixelfed: _recvMsg: searching tag = {search_tag}")

                    # query the whiteboard based on the category/tag
                    # obtain the current last index for the category
                    # while loop to download any videos between last index seen and current.

                    try:
                        with requests.get(f'{self.wb_hostname}:5000/latest/{search_tag}') as resp:
                            diagPrint(f'resp = {resp}')

                            if resp.status_code == 200:
                                resp_json = resp.json()
                                wb_cur_index = resp_json ['latest']
                                wb_old_index = cat_indices.get(search_tag, 0)

                                for wb_index in range (wb_old_index, wb_cur_index):
                                    diagPrint(f'requesting {self.wb_hostname}:5000/get/{search_tag}/{wb_index}')
                                    with requests.get (f'{self.wb_hostname}:5000/get/{search_tag}/{wb_index}') as resp2:
                                        if resp2.status_code == 200:
                                            b64_resp_str = resp2.json()
                                            _imgIn = base64.b64decode(b64_resp_str["data"])
                                            cat_indices[search_tag] = wb_index + 1

                                            with self.recvLock:
                                                self.recvQueue.append (_imgIn)
                                                self.recvLock.notify ()
                                            self.inactive_count = 0

                                            if not Whiteboard.WB_STATUS:
                                                Whiteboard.WB_STATUS = True
                                                Whiteboard.WB_STATUS_CHANGE_TIME = time.time()
                                else:
                                    diagPrint('sleeping for up to 10 secs')
                                    time.sleep(random.randrange(loop_delay))
                                    break

                    except Exception as e:
                        diagPrint(f'caught exception {e}')

            # Sleep before next crawl; the duration is specified in the JSON
            #diagPrint (f"going to sleep for {loop_delay}")
            
            if self.inactive_count < 20:
                time.sleep (loop_delay)
            elif self.inactive_count < 100:
                time.sleep (3 * loop_delay)
            elif self.inactive_count < 600:
                time.sleep (random.randrange(15))
            else:
                time.sleep (random.randrange(30))


    def getMaxSendMsgCount(self):
        return 1

    
    # Send a message.  Return True if successful, False if retry.

    def sendMsg (self, destContext, msgList):
        with Whiteboard._PusherMutex:
            return self._sendMsgMutex (destContext, msgList)


    def _sendMsgMutex (self, destContext, msgList):
        loop_delay = self.wbInstance.get ('loop_delay', 1)

        diagPrint (f"In Pixelfed sendMsg: {len(msgList)} destContext = {destContext}")
        maxCount = self.getMaxSendMsgCount ()
        self.inactive_count = 0

        if not self.userModel.isGood:
            diagPrint (f"Pixelfed: User Model Limit Exceeded")
            return False

        if len(msgList) > maxCount:
            diagPrint (f"Pixelfed: too many messages ({len(msgList)}) for upload... limit to {maxCount}")
            return False

        if len(msgList) == 0:
            diagPrint (f"Pixelfed: empty msgList")
            return False

        result = False
        steg_file_list = ''
        image_bytes = 0 # for user model tracking

        _tmpDir = '/data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/TMP' if 'ANDROID_BOOTLOGO' in os.environ else '/tmp'

        for msg in msgList:
            fd, stego_path = tempfile.mkstemp (suffix = '.jpg', dir = _tmpDir, text = False)
            os.write (fd, msg)
            os.close (fd)
            image_bytes = image_bytes + len (msg)
            
            _, userContext = destContext
            wb_tags = userContext.get ('tags')
            _pTag = wb_tags.get ('pulling')

            diagPrint (f"User Context Pulling is {_pTag}")
        
            # Append time-based dynamic tag

            _dynTags = DynamicTags.dynamicTagsFor (_pTag, self.min_num_tags, self.max_num_tags)
            tags     = _dynTags.tags()

            cnt = random.randint(1,10) % 2

            diagPrint (f'len (tags) = {len (tags)}, cnt = {cnt}, tags = {tags}, min_tags = {self.min_num_tags}, max_tags = {self.max_num_tags}')
            
            while (cnt > 0):
                tags.pop(random.randrange(len(tags)))
                cnt = cnt - 1
                diagPrint (f'len (tags) = {len (tags)}, cnt = {cnt}, tags = {tags}')

                #cnt = random.randint(1,10) % 2

                #while (cnt > 0):
                #    tags.append ('#' + self.doc_gen.word())
                #    cnt = cnt - 1
                
            random.shuffle(tags)
            tag      = tags[0]
            tags = ' '.join(tags)

            _loop_count = 2
        
            while _loop_count:     # "do once" loop that permits graceful exit
                try:
                    with open(stego_path, "rb") as steg_file:
                        encoded_string = base64.b64encode(steg_file.read())
                        
                    # send video with category "tag" and "stego_file_path"
                        
                    diagPrint(f'Posting using tag: {tag[1:]}')
                    with requests.post(f'{self.wb_hostname}:5000/post/{tag[1:]}', 
                                       headers={'Content-Type': 'application/json'},
                                       json={'data': encoded_string},
                                       verify=False) as resp:
                        if resp.status_code != 201:
                            raise Exception (f"json post failed with {result.status_code}")

                    result = True
                    time.sleep(random.randrange(loop_delay))
                    
                    break       # terminate the "do once" loop
            
                except Exception as e:
                    _loop_count -= 1
                    if _loop_count:
                        diagPrint (f"Retrying message send: {e}")
                
            os.remove (stego_path)

        return result    # return status




