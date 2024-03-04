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
from datetime import datetime
from urllib.parse import quote

import requests
from urllib3.exceptions import InsecureRequestWarning
from pathlib import Path


from AbsWhiteboard import AbsWhiteboard
from DiagPrint import diagPrint
from DynamicTags import DynamicTags
from DynamicWords import DynamicWords
from DynamicPhrases import DynamicPhrases


# max sleep interval for explicit wait calls
max_sleep = 20

# comment lists                                                                                                                                  
likelist = ['nice video', 'terrifc', 'awesome', 'very good', 'excellent', 'amazing', 'magnificent', '2 thumbs up!', 'wonderful', 'wow!!', 'I cant stop listening to this song every time coz I love it', 'what a great video!', 'This is so refreshing', 'LoL', 'Congratulations', 'I am glad to see so many views']
dislikelist = ['boring', 'ok', 'blah blah blah', 'really?', 'bad idea', 'disgusting', 'poor video', 'sad story', 'haters are going to hate', 'I have nothing to do with this video', 'What did I just watch?', 'Avideo deserves better']




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

    _DEFAULT_MIN_NUM_TAGS = 1
    _DEFAULT_MAX_NUM_TAGS = 1

    
    _PusherDriver = None
    _PusherClosed = False
    _PusherMutex  = RLock ()

    recv_msg_list = []
    wb_hostname = ""


    @staticmethod
    def _listfromdict (_dict, _key):
        _list = _dict.get (_key, None)
        return _list if isinstance (_list, list) else None

    def __init__ (self, user, credentials, tags, wbInstance, wbCConfig):

        # Prevent direct instantiation of this class

        diagPrint("Avideo: __Init__")

        _type = type (self)
        #_type = None

        if _type == __class__:
            raise NotImplementedError ('{} may not be instantiated'.format (_type))

        # Initialization

        super ().__init__ (user, credentials, tags, wbInstance, wbCConfig)

        self.user       = user
        self.wbInstance = wbInstance

        self.min_num_tags = wbCConfig.get ('min_num_tags', self._DEFAULT_MIN_NUM_TAGS)
        self.max_num_tags = wbCConfig.get ('max_num_tags', self._DEFAULT_MAX_NUM_TAGS)
        self.inactive_count = 0
        self.wb_hostname = wbInstance.get('url', None)

        if self.wb_hostname:
            self.wb_hostname = self.wb_hostname.replace('https', 'http')

        self.dynTagsBrdcst  = []
        self.dynTagsPulling = None

        if isinstance (tags, dict):
            _tagList = self._listfromdict (tags, 'broadcast')
            
            if _tagList:
                for _tag in _tagList:
                    self.dynTagsBrdcst.append (DynamicTags.dynamicTagsFor (_tag + 'a', self.min_num_tags, self.max_num_tags))

            _tag = tags.get ('pulling', None)
            diagPrint (f"Avideo Tags = {_tag}")

            if isinstance (_tag, str):
                self.dynTagsPulling = DynamicTags.dynamicTagsFor (_tag + 'a', self.min_num_tags, self.max_num_tags)
                
        elif isinstance (tags, str):
            self.dynTagsPulling = DynamicTags.dynamicTagsFor (tags + 'a', self.min_num_tags, self.max_num_tags)
            
        isgood = self.dynTagsBrdcst or self.dynTagsPulling
            
        if not isgood:
            raise KeyError ('Missing "tags" or subkeys')

        self.recvThread = None
        self.recvLock   = Condition ()
        self.recvListLock = Condition ()	
        self.recvQueue  = []
        self.recvMutex  = Condition ()
 
        self._url_cache = _SharedCache.getSingleton ()


    # Use credentials, wbInstance, and wbCConfig maps to open and return a channel.
    #
    # user           # 'Bob Evans'
    # credentials    # {'account': 'BobEvans', 'password': '@bob_evans312'}
    # userContext    # {'tags': {'broadcast': ['#washington', '#wdc'],
    #                            'pushing': ['#monument', '#senate'],
    #                            'pulling': ['#scotus', '#omb']
    #                           }
    # wbInstance     # {'class': 'Avideo', 'url': 'https://destini02.csl.sri.com'}
    # wbCConfig      # {'driver_path': '/usr/local/bin/geckodriver',
    #                   'connection_duration': 600,
    #                   'initial_retry_wait': 4,
    #                   'max_retry_count': 5,
    #                   'next_wait_lambda': 'lambda _t: 2 * _t # exponential backoff'}

    def openChannel (self, user, credentials, _unused, wbInstance, wbCConfig):
        return True

    
    # Close the channel

    def closeChannel (self, channel):
        self._channel = None



    @staticmethod
    def _makeTempPath (suffix = None, prefix = None, dir = None, text = False, callback = None):
        _fd, _path = tempfile.mkstemp (suffix = suffix, prefix = prefix, dir = dir, text = text)
        os.close (_fd)

        if callback:
            Whiteboard._removePath (_path)
            callback (_path)

        return _path


    def unpackMessages (self, blob, blen):
        idx = 0

        with self.recvListLock:
            while (idx < blen):
                mlen = int.from_bytes(blob[idx:idx+4], 'big')
                msg = blob[idx+4:idx+4+mlen]
                self.recv_msg_list.append (msg)
                m = hashlib.new ('md5')
                m.update(msg[49:mlen])
                diagPrint(f'Unpacked Message: {m.hexdigest()} {mlen}')            
                idx = idx + mlen + 4


    # Wait for and return inbound message 
    def recvMsg (self, userContext):
        
        with self.recvListLock:
            if len (self.recv_msg_list) > 0:
                return self.recv_msg_list.pop (0)

        if self.recvThread is None:
            _t_name = 'Avideo-recvMsg-{}'.format (self.user)
            self.recvThread = self.startThread (_t_name, self._recvMsg, (userContext, ))

        while self._channel:    # accommodate the channel being asynchronously closed
            with self.recvLock:
                if self.recvQueue:
                    vid_path = self.recvQueue.pop (0)
                    
                    diagPrint (f'popping 1... input: {vid_path}')

                    if not True:
                        return vid_path

                    msg_path = self._makeTempPath (suffix = '.bin', dir = '/tmp')

                    diagPrint (f'calling video_unwedge with {vid_path} {msg_path}')

                    fsize = Path(vid_path).stat().st_size
                    uw_proc_stat = None

                    if fsize < 20000000:
                        uw_proc_stat = subprocess.run (['/usr/local/lib/race/comms/DestiniAvideo/scripts/video_unwedge2', '-message', msg_path, '-bpf', '1', '-nfreqs', '2', '-maxfreqs', '8', '-ecc', '20', '-quality', '88', '-mcudensity', '40', '-steg', vid_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

                        diagPrint (f'video_unwedge2 trial 1 return code: {uw_proc_stat.returncode}')

                        if Path(msg_path).stat().st_size == 0:
                            uw_proc_stat.returncode = 1

                    if fsize >= 20000000 or uw_proc_stat.returncode != 0:
                        uw_proc_stat = subprocess.run (['/usr/local/lib/race/comms/DestiniAvideo/scripts/video_unwedge', '-message', msg_path, '-bpf', '1', '-nfreqs', '4', '-maxfreqs', '4', '-quality', '30', '-steg', vid_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
                        diagPrint (f'video_unwedge trial 2 return code: {uw_proc_stat.returncode}')
                        
                    # proc_stat = subprocess.run (['video_unwedge', '-message', msg_path, '-seed', '5', '-quality', '30', '-ecc', '12', '-steg', vid_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
                    

                    with open (msg_path, 'rb') as f_in:
                        _blob = f_in.read()

                    blob_len = len(_blob)

                    if blob_len == 0:
                        diagPrint (f'video_unwedge blob size 0')                        
                        continue
                    else:
                        diagPrint (f'video_unwedge recovered blob len {blob_len}')
                        
                    
                    self.unpackMessages (_blob, blob_len)
                    #    os.remove(vid_path)
                    os.remove(msg_path)

                    with self.recvListLock:
                        return self.recv_msg_list.pop (0)
                    
                else:
                    self.recvLock.wait ()

        return None

    def _recvMsg (self, userContext):

        loop_delay = self.wbInstance.get ('loop_delay', 1)
        prev_count = 0

        # key:category, value:last index 
        cat_indices = {}

        diagPrint("In _recvMsg_")

        # Poll for forever or until the channel is closed

        while True:    # accommodate the channel being asynchronously closed

            # Search last three tag intervals, starting with "now".
            
            bDynTags = []
            for _dynTagBrdcst in self.dynTagsBrdcst:
                bDynTags.extend (list (map (_dynTagBrdcst.words, [0, -1])))
            pDynTags = list (map (self.dynTagsPulling.words, [0, -1]))
            
            dynTags = bDynTags
            dynTags.extend (pDynTags)
            self.inactive_count = self.inactive_count + 1
            
            for search_tags in dynTags:
                search_tag      = search_tags[random.randrange (len (search_tags))]
                                
                diagPrint(f"_recvMsg: searching tag = {search_tag}")

                # Search for time-based dynamic word (viz., tag without leading '#')
                # Note: we're not using tags in 'broadcast'

                while True:         # "do once" loop that permits early exits
                    try:
                        # query the whiteboard based on the category/tag
                        # obtain the current last index for the category
                        # while loop to download any videos between last index seen and current.
                     
                        with requests.get(f'{self.wb_hostname}:5000/latest/{search_tag}') as resp:
                            if resp.status_code == 200:
                                resp_json = resp.json()
                                wb_cur_index = resp_json ['latest']
                                wb_old_index = cat_indices.get(search_tag, 0)

                                for wb_index in range (wb_old_index, wb_cur_index):
                                    diagPrint(f'requesting {self.wb_hostname}:5000/get/{search_tag}/{wb_index}')
                                    with requests.get (f'{self.wb_hostname}:5000/get/{search_tag}/{wb_index}') as resp2:
                                        if resp2.status_code == 200:
                                            b64_resp_str = resp2.json()
                                            _vidIn = base64.b64decode(b64_resp_str["data"])
                                            cat_indices[search_tag] = wb_index + 1                                    
                                            vid_path = self._makeTempPath (suffix = '.mp4', dir = '/tmp')

                                            with open (vid_path, 'wb') as f_out:
                                                f_out.write (_vidIn)

                                            diagPrint (f'calling ffmpeg with {vid_path}')

                                            proc_stat = subprocess.run (['ffmpeg', '-i', vid_path, '-f', 'null', '-'], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

                                            if proc_stat.returncode == 0:                     
                                                with self.recvLock:
                                                    self.recvQueue.append (vid_path)
                                                    self.recvLock.notify ()
                                                    break

                                        else:
                                            break
                                    time.sleep(random.randrange(loop_delay))
                            else:
                                time.sleep(random.randrange(loop_delay))
                                break
                    except:
                        diagPrint (f"Exception error 2: {sys.exc_info ()[0]}")
                        if Whiteboard.WB_STATUS or Whiteboard.WB_STATUS_CHANGE_TIME == 0:
                            Whiteboard.WB_STATUS_CHANGE_TIME = time.time()                        
                        Whiteboard.WB_STATUS = False
               
                        time.sleep (15)
                        continue

    

                    if not Whiteboard.WB_STATUS:
                        Whiteboard.WB_STATUS = True
                        Whiteboard.WB_STATUS_CHANGE_TIME = time.time()
                        time.sleep (random.randrange(3))
                        
                    break           # "do once"
            
            if self.inactive_count < 20:
                time.sleep (loop_delay)
            elif self.inactive_count < 100:
                time.sleep (3 * loop_delay)
            elif self.inactive_count < 600:
                time.sleep (random.randrange(15))
            else:
                time.sleep (random.randrange(30))
            

    def packMessages (self, msgList):
        blob = bytearray()
        
        for j in range(len(msgList)):
            mlen = len(msgList[j])
            c = mlen.to_bytes(4, 'big')
            blob.extend(c) 
            blob.extend(msgList[j])
            m = hashlib.new ('md5')
            m.update(msgList[j][49:mlen])
            diagPrint(f'Adding Message to Send: {m.hexdigest()} {mlen-49}')            
        return blob


    

    def getMaxBlobSize (self):
        return 1300000
 
    def getMaxSendMsgCount(self):
        return 500


    # Send a message.  Return True if successful, False if retry.

    def sendMsg (self, destContext, msgList):
        with Whiteboard._PusherMutex:
            return self._sendMsgMutex (destContext, msgList)


    

    # Send a message.  Return True if successful, False if retry.
    def _sendMsgMutex (self, destContext, msgList):
        loop_delay = self.wbInstance.get ('loop_delay', 1)
        
        diagPrint (f"In Avideo sendMsg: {len(msgList)}")
        maxCount = self.getMaxSendMsgCount ()
        self.inactive_count = 0

        if len(msgList) > maxCount:
            diagPrint (f"Avideo: too many messages ({len(msgList)}) for upload... limit to {maxCount}")
            return False

        if len(msgList) == 0:
            diagPrint (f"Avideo: empty msgList")
            return False
        
        result = False

        msg = self.packMessages (msgList)
        msg_len = len (msg)
        encode_type = 1
        
        diagPrint(f"message size is: {msg_len}")
        diagPrint(f"message contents are: {msg}")

        stego_file_path = tempfile.mktemp (suffix = '.mp4', dir = '/tmp')

        if msg_len < 500:
            coverlist = ['coast-00.mp4',]
            encode_type = 2
        elif msg_len < 1000:
            #cz0.mp4
            coverlist = ['worship0.mp4',]
            encode_type = 2
        elif msg_len < 5000:
            coverlist = ['butterfly1.mp4',]
            encode_type = 2 
        elif msg_len < 10000:
            coverlist = ['gekas-sweden-1.mp4',]
            encode_type = 2
        elif msg_len < 130000:
            coverlist = ['crows1_130_norm.mp4',]
        elif msg_len <= 320000:
            coverlist = ['crows1_320_norm.mp4',]
        elif msg_len < 1300000:
            coverlist = ['yubatake-5_out.mp4',]
        else:
            diagPrint (f"Message size too large .... {msg_len}.  Max supported size is 1.3 MB")
            return None

        #this needs to be /ramfs/destini/covers/avideo/ in order to find the refactored video covers
        coverfile = '/ramfs/destini/covers/video/' + coverlist[random.randrange(len(coverlist))] # random.choice(coverlist)
        msg_path = self._makeTempPath (suffix = '.bin', dir = '/tmp')
        
        with open (msg_path, 'wb') as f_out:
            f_out.write (msg)


        diagPrint (f'calling video_wedge with -message of size {msg_len}, -cover {coverfile} -message {msg_path} {msg_len}')
        diagPrint (f"message path before encoding is {msg_path}")

        if encode_type == 1:
            proc_stat = subprocess.run (['/usr/local/lib/race/comms/DestiniAvideo/scripts/video_wedge', '-cover', coverfile, '-bpf', '1', '-mcudensity', '25', '-qp', '10', '-nfreqs', '4', '-maxfreqs', '4', '-message', msg_path, '-jpeg_quality', '30', '-output', stego_file_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

        else:
            proc_stat = subprocess.run (['/usr/local/lib/race/comms/DestiniAvideo/scripts/video_wedge2', '-cover', coverfile, '-bpf', '1', '-mcudensity', '40', '-nfreqs', '2', '-maxfreqs', '8', '-ecc', '20', '-message', msg_path, '-jpeg_quality', '88', '-output', stego_file_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

            
            
        
        diagPrint (f'video_wedge return code: {proc_stat.returncode}')

        wedge_log = self._makeTempPath (prefix = 'auw-', suffix = '.log', dir = '/tmp')
        with open (wedge_log, 'wb') as _log_out:
            _log_out.write (proc_stat.stdout)

        diagPrint(f"message path to be removed is {msg_path}")

        os.remove (msg_path)
        diagPrint (f"stego_file_path = {stego_file_path}")

        _, userContext = destContext
        wb_tags = userContext.get ('tags')

        #_tags   = list (wb_tags.get ('broadcast'))
        _pTag    = wb_tags.get ('pulling')

        
        # adding 'a'to ensure the set of tags for Pixelfed and Avideo are different
        _dynTags = DynamicTags.dynamicTagsFor (_pTag + 'a', self.min_num_tags, self.max_num_tags)
        tags     = _dynTags.tags()
        tag      = tags[0]
        _loop_count = 2
        
        while _loop_count:     # "do once" loop that permits graceful exit
            try:

                if self._channel is None:   # accommodate the channel being asynchronously closed
                    diagPrint ("Avideo:sendMsg (): detected closed channel")
                    break

                with open(stego_file_path, "rb") as steg_file:
                    encoded_string = base64.b64encode(steg_file.read())

                # send video with category "tag" and "stego_file_path"
                #
                diagPrint(f'Posting using tag: {tag[1:]}')
                with requests.post(f'{self.wb_hostname}:5000/post/{tag[1:]}', 
                                   headers={'Content-Type': 'application/json'},
                                   json={'data': encoded_string},
                                   verify=False) as resp:

                    if resp.status_code != 201:
                        raise Exception (f"json post failed with {resp.status_code}")
                 
                time.sleep(random.randrange(loop_delay))
       
                if self._channel is None:   # accommodate the channel being asynchronously closed
                    diagPrint ("Avideo:sendMsg (): detected closed channel")
                    break

                diagPrint("In Avideo SendMSG 5: Terminating do once loop")
                result = True

                file_size = os.path.getsize(stego_file_path)
                self.trackAdd (nItems = len(msgList), nBytes = file_size)

                if len(msgList) == 1 and msg_len < 10000:
                    time.sleep (random.randrange(loop_delay))
                    
                break       # terminate the "do once" loop
            
            except Exception as e:
                _loop_count -= 1

                if _loop_count:
                    diagPrint (f"Retrying message send: {e}")
                                
        # os.remove (stego_file_path)
        return result    # return status


