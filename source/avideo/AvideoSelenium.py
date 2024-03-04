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
from bs4 import BeautifulSoup
from selenium import webdriver
from seleniumrequests import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
# for explicit wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

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


# Per Steven, disable warnings for unverified https
# https://stackoverflow.com/questions/27981545/suppress-insecurerequestwarning-unverified-https-request-is-being-made-in-pytho

#requests.packages.urllib3.disable_warnings (category = InsecureRequestWarning)

def safe_str(obj):
    return obj.encode('ascii', 'ignore').decode('ascii')


def wait_catch_exception(driver, max_sleep, selector_type, selector, msg):
    element = None

    try:
#        diagPrint (f"in wait catch exception {msg}")
        element = WebDriverWait(driver, max_sleep).until(
            EC.presence_of_element_located((selector_type, selector)))
#        diagPrint (f"done with webdriver wait {msg}")
    except TimeoutException:
        diagPrint (f"Timeout Exception: {msg}")
        return None
    except:
        diagPrint (f"Other Exception: {msg}, {sys.exc_info ()[0]}")
        return None
    
    return element


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

    
    _PusherDriver = None
    _PusherClosed = False
    _PusherMutex  = RLock ()

    recv_msg_list = []


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

    def _openDriver (self):
        user           = self._user
        credentials    = self._cred
        wbInstance     = self._inst
        wbCConfig      = self._cconfig

        wb_class       = wbInstance.get ('class', None)
        encoder_url         = wbInstance.get ('encoder_url', None)
        wb_driver_path = wbCConfig.get  ('driver_path', None)
        streamer_url   = wbInstance.get ('url', None)
        wb_credentials = credentials if credentials else wbInstance.get ('credentials', None) 

        if (wb_class != 'Avideo') or (encoder_url == None) or (wb_driver_path == None):
            return None

        diagPrint ("In Avideo Open Channel")

        wb_user =  wb_credentials.get ('account',  None)
        wb_pass  = wb_credentials.get ('password', None)

        if (wb_user == None or wb_pass == None):
            return None

        ##############################
        # webdriver setup
        #firefox_options = webdriver.FirefoxOptions()
        #firefox_options.add_argument("--headless")

        firefox_options = Options()

        # uncomment the following to enable headless mode
        firefox_options.headless = True


        try:
            firefox_profile = webdriver.FirefoxProfile()
            firefox_profile.set_preference("network.prefetch-next", False)
            firefox_profile.set_preference("accept_untrusted_certs", True)
            driver = webdriver.Firefox(options=firefox_options, firefox_profile=firefox_profile, executable_path=wb_driver_path)
            
            #driver = webdriver.Firefox (options = firefox_options, seleniumwire_options = {'verify_ssl': False, 'connection_timeout': None}, executable_path = wb_driver_path)
            #driver = webdriver.Firefox (options = options, executable_path = wb_driver_path)
           
            # implicit wait tells WebDriver to poll the DOM for a certain amount of time
            # when trying to find any element (or elements) not immediately available
            # Once set, the implicit wait is set for the life of the WebDriver object

            # driver.set_timeout (30)
            driver.implicitly_wait (30) # sec
            driver.set_page_load_timeout (30)
            #driver.set_window_size (1300,900)
            #driver.set_window_position (10,10)


            login_url = os.path.join (streamer_url, 'user')


            num_tries = 5

            while num_tries > 0:
                diagPrint (f"login url = {login_url}")

                try:
                    driver.get (login_url)
                    driver.find_element_by_css_selector ('input[id=inputUser]').send_keys (wb_user)
                    driver.find_element_by_css_selector ('input[id=inputPassword]').send_keys (wb_pass)
                except Exception as e:
                    num_tries = num_tries - 1
                    if Whiteboard.WB_STATUS or Whiteboard.WB_STATUS_CHANGE_TIME == 0:
                        Whiteboard.WB_STATUS_CHANGE_TIME = time.time ()
                    Whiteboard.WB_STATUS = False
                    time.sleep(5)
                    continue

                diagPrint("avideo login 0")
            
 
                if not Whiteboard.WB_STATUS:
                    Whiteboard.WB_STATUS = True
                    Whiteboard.WB_STATUS_CHANGE_TIME = time.time()



                diagPrint("avideo login 1")
                element = wait_catch_exception (driver, max_sleep, By.CSS_SELECTOR, "button[id=mainButton]",
                                            "Explicit wait error for login/submit")


                diagPrint("avideo login 2")
            
                if (element == None):
                    num_tries = num_tries - 1
                    time.sleep(5)
                    continue

                diagPrint("HERE 3")

                driver.find_element_by_css_selector ('button[id=mainButton]').click ()
                element = wait_catch_exception (driver, max_sleep, By.CSS_SELECTOR, ".fa-sign-out-alt",
                                                "Unexplained login failure")
                if element == None:
                    num_tries = num_tries - 1
                    time.sleep(5)
                    continue

                diagPrint("Logged into Avideo")
                break        
        except:
             diagPrint (f"Avideo: Exception error 1: {sys.exc_info ()[0]}")
             return None

        num_tries = 5

        diagPrint ("Logging into encoder")

        try:
            
            while num_tries > 0:
                diagPrint(f"encoder url = {encoder_url}")

                try:
                    driver.get (encoder_url)
                    
                    diagPrint("encoder login 1")
                    element = wait_catch_exception (driver, max_sleep, By.CSS_SELECTOR, "button[id=mainButton]",
                                                "Explicit wait error for encoder login/submit") 

                    diagPrint("encoder login 2")

                    if element == None:
                        num_tries = num_tries - 1
                        time.sleep(5)
                        continue
                
                    driver.find_element_by_css_selector('input[id=siteURL]').clear()
                    driver.find_element_by_css_selector('input[id=siteURL]').send_keys(streamer_url.replace("https", "http"))
                    driver.find_element_by_css_selector('input[id=inputUser]').send_keys(wb_user)
                    driver.find_element_by_css_selector('input[id=inputPassword]').send_keys(wb_pass)
                    driver.find_element_by_css_selector('button[id=mainButton]').click()

                except Exception as e:
                    num_tries = num_tries - 1
                    if Whiteboard.WB_STATUS or Whiteboard.WB_STATUS_CHANGE_TIME == 0:
                        Whiteboard.WB_STATUS_CHANGE_TIME = time.time ()
                    Whiteboard.WB_STATUS = False
                    time.sleep(5)
                    continue


                element = wait_catch_exception (driver, max_sleep, By.CSS_SELECTOR, ".glyphicon-log-out",
                                                "Unexplained login failure")
                if element != None:
                    break;
                num_tries = num_tries - 1
                
        except:
            diagPrint (f"Exception error logging into encoder url: {sys.exc_info ()[0]}")
            return None

        element = wait_catch_exception (driver, max_sleep, By.ID, "upload",
                                        "Encoder login timeout")
        if element == None:
            diagPrint ("Login Failed")
            return None

        resp = safe_str(driver.page_source)
    
        if "Logoff" in resp:
            diagPrint ("Login Successful!")
        else:
            diagPrint ("Login Failed")

            with open('login.html', 'w') as f:
                f.write(resp)
                return None

        return driver     # subclass must implement and return channel object


    
    # Close the channel

    def closeChannel (self, channel):
        if isinstance (channel, bool):
            return
        
        if channel:
            if channel == Whiteboard._PusherDriver:
                if Whiteboard._PusherClosed:
                    return
                else:
                    Whiteboard._PusherClosed = True
                    
            channel.close ()




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
        if self._channel is None or isinstance (self._channel, bool):
            self._channel = self._openDriver()

        loop_delay = self.wbInstance.get ('loop_delay', 1)
        prev_count = 0
        rand_wait_flag = 0

        diagPrint("In _recvMsg_")

        # Poll for forever or until the channel is closed

        while self._channel:    # accommodate the channel being asynchronously closed

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
                search_url_base = self.wbInstance.get ('url')
                search_url      = search_url_base +  "/?search=" +  search_tag
                diagPrint(f"_recvMsg: searching tag = {search_tag} {search_url}")

                
                # Search for time-based dynamic word (viz., tag without leading '#')
                # Note: we're not using tags in 'broadcast'

                while True:         # "do once" loop that permits early exits
                    try:
                        self._channel.get (search_url)
                    except:
                        diagPrint (f"Exception error 2: {sys.exc_info ()[0]}")
                        if Whiteboard.WB_STATUS or Whiteboard.WB_STATUS_CHANGE_TIME == 0:
                            Whiteboard.WB_STATUS_CHANGE_TIME = time.time()                        
                        Whiteboard.WB_STATUS = False
                        self._closeChannel ()
                        self._channel = None

                        while self._channel == None:
                            time.sleep (15)
                            self._channel = self._openDriver()
                        break           
                    finally:
                        self.setTimer ('searchURL', False)
    
                    if rand_wait_flag > 0:
                        rand_wait_flag = rand_wait_flag - 1
                        time.sleep(0.5)
                    else:
                        time.sleep (random.randrange (3))


                    if not Whiteboard.WB_STATUS:
                        Whiteboard.WB_STATUS = True
                        Whiteboard.WB_STATUS_CHANGE_TIME = time.time()
                    
                    html_source = self._channel.page_source
                    soup = BeautifulSoup(html_source, features="html.parser")
            
                        
                    # for the 1st match
                    storage_urls = []
                    
                    video_urls = soup.findAll('source')
                    for video_url in video_urls:
                        if "_HD.mp4" in video_url['src'] and not self._url_cache.isCached (video_url['src']):
                            storage_urls.append(video_url['src'])
                            diagPrint (video_url['src'])

                    #additional thumbnails         
                    images = soup.findAll('img')
                    
                    for image in images:
                        image_datasrc = image.get('data-src')
                        if not image_datasrc:
                            # diagPrint ("cannot find data-src") 
                            continue

                        if ".webp" in image['data-src']:
                            diagPrint (f".webp link: {image['data-src']}")
                            # construct the url for the HD link
                            hd_link = image_datasrc.replace(".webp", "_HD.mp4")
                            diagPrint (f"hd link: {hd_link}")
                            
                            if hd_link in storage_urls or self._url_cache.isCached (hd_link):
                                diagPrint (f"already found: {hd_link}")
                            else:
                                diagPrint (f"adding: {hd_link}")
                                storage_urls.append(hd_link)

                    # debug
                    diagPrint (f"storage_urls : {format(storage_urls)}")

    
                    if storage_urls:
    
                        ##############################
                        # selenium doesn't seem to support one to download a file (e.g., jpeg file) directly
                        # we construct a get request (need to import requests) with the user-agent string
                        # and cookie used by selenium
    
                        # find the cookies used by selenium
                        try:
                            selenium_cookies = self._channel.get_cookies ()
                        except:
                            self.incrementStatus ('getCookiesError')
                            diagPrint (f"Avideo Exception error: couldn't get cookies; {sys.exc_info ()[0]}")
                            break           # TBD: is this a pathological failure?
    
                        cookies = {
                            'value': selenium_cookies[0].get ('value'),
                        }
    
                        try: 
                            # find the user-agent string used by selenium
                            user_agent = self._channel.execute_script ("return navigator.userAgent;")
                        except:
                            self.incrementStatus ('getUserAgentError')
                            diagPrint (f"Avideo Exception error 5: couldn't get useragent; {sys.exc_info ()[0]}")
                            break           # TBD: is this a pathological failure?
    
                        headers = {
                            'User-Agent': user_agent,
                        }
    
                        for url in storage_urls:
                            try:
                                cnt = 0
                                while cnt < 3:
                                    self.inactive_count = 0
                                    diagPrint(f"Downloading Video: {search_tag} {url}")
                                    response = requests.get (url, cookies = cookies, headers = headers, verify = False)
                                    _vidIn = response.content
                                    vid_path = self._makeTempPath (suffix = '.mp4', dir = '/tmp')
                                                        
                                    with open (vid_path, 'wb') as f_out:
                                        f_out.write (_vidIn)

                                    diagPrint (f'calling ffmpeg with {vid_path}; cnt = {cnt}')

                                    proc_stat = subprocess.run (['ffmpeg', '-i', vid_path, '-f', 'null', '-'], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
                                    
                                    if proc_stat.returncode == 0:                     
                                        with self.recvLock:
                                            self._url_cache.cache (url)
                                            self.recvQueue.append (vid_path)
                                            self.recvLock.notify ()
                                            break
                                        
                                    time.sleep(random.randrange(2))
                                    cnt = cnt + 1
                            except:
                                diagPrint (f"Avideo Exception err: url fetch failed; {sys.exc_info ()[0]}")
                        time.sleep (random.randrange(3))
                    break           # "do once"
            
            if self.inactive_count < 20:
                time.sleep (loop_delay)
            elif self.inactive_count < 100:
                time.sleep (3 * loop_delay)
                self.sendMsgGood (userContext)
            elif self.inactive_count < 600:
                time.sleep (random.randrange(15))
                self.sendMsgGood (userContext)
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

        if Whiteboard._PusherDriver is None:
            Whiteboard._PusherDriver = self._openDriver()

        self._channel = Whiteboard._PusherDriver

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
        
        stego_file_path = tempfile.mktemp (suffix = '.mp4', dir = '/tmp')

        if msg_len < 500:
            coverlist = ['coast-00.mp4', 'cz-00.mp4', 'gelding-00.mp4', 'times-00.mp4', 'worship-00.mp4']
            encode_type = 2
        elif msg_len < 1000:
            #cz0.mp4
            coverlist = ['worship0.mp4', 'gekas0.mp4', 'butterfly0.mp4', 'anna0.mp4', 'alaska0.mp4', 'gekas0_2.mp4']
            encode_type = 2
        elif msg_len < 5000:
            coverlist = ['butterfly1.mp4', 'butterfly2.mp4', 'worship.mp4', 'gelding1.mp4', 'cz2Av-2.mp4', 'bullfinch.mp4', 'gekas-sweden-1-1.mp4']
            encode_type = 2 
        elif msg_len < 10000:
            coverlist = ['gekas-sweden-1.mp4', 'bird-short-1.mp4', 'czech-street-2.mp4']
            encode_type = 2
        elif msg_len < 130000:
            coverlist = ['crows1_130_norm.mp4', 'crows2_130_norm.mp4', 'jpshibuya_130_norm.mp4',
                         'osaka1_130_norm.mp4', 'yubatake2_130_norm.mp4', 'yubatake3_130_norm.mp4',
                         'yubatake4_130_norm.mp4']
        elif msg_len <= 320000:
            coverlist = ['crows1_320_norm.mp4', 'crows2_320_norm.mp4', 'jpshibuya_320_norm.mp4',
                        'osaka1_320_norm.mp4',   'yubatake1_320_norm.mp4', 'yubatake2_320_norm.mp4', 
                        'yubatake5_320_norm.mp4']
        elif msg_len < 1300000:
            coverlist = ['yubatake-5_out.mp4', 'osaka-dotonbori-3_out.mp4']

        elif msg_len < 2100000:
            coverlist = ['yubatake-6.out.mp4']
        else:
            diagPrint (f"Message size too large .... {msg_len}.  Max supported size is 1.3 MB")
            return None

        #this needs to be /ramfs/destini/covers/avideo/ in order to find the refactored video covers
        coverfile = '/ramfs/destini/covers/video/' + coverlist[random.randrange(len(coverlist))] # random.choice(coverlist)
        msg_path = self._makeTempPath (suffix = '.bin', dir = '/tmp')
        
        with open (msg_path, 'wb') as f_out:
            f_out.write (msg)


        diagPrint (f'calling video_wedge with -message of size {msg_len}, -cover {coverfile} -message {msg_path} {msg_len}')


        if encode_type == 1:
            proc_stat = subprocess.run (['/usr/local/lib/race/comms/DestiniAvideo/scripts/video_wedge', '-cover', coverfile, '-bpf', '1', '-mcudensity', '25', '-qp', '10', '-nfreqs', '4', '-maxfreqs', '4', '-message', msg_path, '-jpeg_quality', '30', '-output', stego_file_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

        else:
            proc_stat = subprocess.run (['/usr/local/lib/race/comms/DestiniAvideo/scripts/video_wedge2', '-cover', coverfile, '-bpf', '1', '-mcudensity', '40', '-nfreqs', '2', '-maxfreqs', '8', '-ecc', '20', '-message', msg_path, '-jpeg_quality', '88', '-output', stego_file_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)

            
            
        
        diagPrint (f'video_wedge return code: {proc_stat.returncode}')

        wedge_log = self._makeTempPath (prefix = 'auw-', suffix = '.log', dir = '/tmp')
        with open (wedge_log, 'wb') as _log_out:
            _log_out.write (proc_stat.stdout)

        

        os.remove (msg_path)
        diagPrint (f"stego_filepath = {stego_file_path}")

        _, userContext = destContext
        wb_tags = userContext.get ('tags')

        #_tags   = list (wb_tags.get ('broadcast'))
        _pTag    = wb_tags.get ('pulling')

        
        # adding 'a'to ensure the set of tags for Pixelfed and Avideo are different
        _dynTags = DynamicTags.dynamicTagsFor (_pTag + 'a', self.min_num_tags, self.max_num_tags)
        tags     = _dynTags.tags()

        cnt = random.randint(1,10) % 3

        while (cnt > 0):
            tags.pop(random.randrange(len(tags)))
            cnt = cnt - 1
        
        tags = ' '.join(tags)

        encoder_url = self.wbInstance.get('encoder_url')
        _loop_count = 2
        
        while _loop_count:     # "do once" loop that permits graceful exit
            try:
                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Avideo:sendMsg (): detected closed channel")
                        break

                    self._channel.get (encoder_url)
                except Exception as e:
                    diagPrint (f"Error getting encoder url: {e} {encoder_url}")
                    raise

                diagPrint("In Avideo SendMSG: 1")
                
                element = wait_catch_exception (self._channel, max_sleep,
                                                By.CSS_SELECTOR, "button[type=submit]",
                                                "Explicit wait error or submit")

                if (element == None):
                    diagPrint ("Avideo:sendMsg (): error waiting for encoder url")
                    diagPrint (f"Page Source = {self._channel.page_source}")
                    raise Exception ("Error waiting for encoderurl")

                             
                diagPrint(f"In Avideo SendMSG: 2: {_pTag} {tags} {coverfile} {stego_file_path}")
                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Avideo:sendMsg (): detected closed channel")
                        break
 
                     #html_source = self._channel.page_source                   
                     #with open('page.html', 'w') as f:
                     #    f.write(safe_str(html_source))


                    diagPrint("In Avideo SendMSG: 3")
                    self._channel.find_element_by_css_selector('input[id=title]').send_keys(DynamicPhrases.getRandomPhrase())
                    self._channel.find_element_by_css_selector('textarea[id=description]').send_keys(tags)
                    time.sleep(0.5)
                    self._channel.find_element_by_css_selector('input[type=file]').send_keys(stego_file_path)
                    time.sleep(0.5)
                                        
                    element = wait_catch_exception (self._channel, max_sleep, By.CSS_SELECTOR, "button[type=submit]",
                                                    "Explicit wait error for login/submit")
                    if (element == None):
                        raise

                    self._channel.find_element_by_css_selector('button[type=submit]').click()
                    time.sleep(2)
                    diagPrint("In Avideo SendMSG: 4")
                    
                    #html_source = self._channel.page_source                   
                    #with open('results.html', 'w') as f:
                    #    f.write(safe_str(html_source))
                        
                except:
                    diagPrint (f"A video encoder failed: {sys.exc_info ()[0]}")
                    raise

                if self._channel is None:   # accommodate the channel being asynchronously closed
                    diagPrint ("Avideo:sendMsg (): detected closed channel")
                    break

                diagPrint("In Avideo SendMSG 5: Terminating do once loop")
                result = True

                file_size = os.path.getsize(stego_file_path)
                self.trackAdd (nItems = len(msgList), nBytes = file_size)

                if len(msgList) == 1 and msg_len < 10000:
                    time.sleep (10)
                    
                break       # terminate the "do once" loop
            
            except Exception as e:
                _loop_count -= 1

                if _loop_count:
                    diagPrint (f"Re-establishing connection: {e}")
                    self._closeChannel ()
                    Whiteboard._PusherDriver = self._openDriver ()
                    self._channel = Whiteboard._PusherDriver

        if result == True:
            try:
                self.avideo_feedback("", random.randint(0,1))
            except Exception as e:
                diagPrint (f"Ignoring error posting feedback: {e}")
                
        os.remove (stego_file_path)
        return result    # return status


    def avideo_feedback (self, search_tag, thumb_pref):
        if random.randint(1,5) != 1:
            return

        diagPrint("IN AVIDEO FEEDBACK...")
        success = True
        commentProb = 0.5

        avideo_base = self.wbInstance.get ('url')

        if search_tag == "":
            search_url = avideo_base
        else:
            search_url = avideo_base + "/?search=" + search_tag

        diagPrint ("search_url: " + search_url)

        try:
            self._channel.get(search_url)
        except Exception as e:
            print (f"Error: driver.get failed {e}")
            success = False

        time.sleep(1)

        html_source = self._channel.page_source
        with open('/tmp/results.html', 'w') as f:
           f.write(html_source)

        if (thumb_pref != 0):
            try:
                soup = BeautifulSoup(html_source, features="html.parser")
                if (thumb_pref > 0):
                    buttonElt = soup.find("a",  id="likeBtn")
                    thumbButton = self._channel.find_element_by_css_selector('a[id=likeBtn]')
                else:
                    buttonElt = soup.find("a",  id="dislikeBtn")
                    thumbButton = self._channel.find_element_by_css_selector('a[id=dislikeBtn]')

                if buttonElt:
                    bclass = buttonElt["class"]

                    if not("myVote" in bclass):
                        thumbButton.click()
                        diagPrint (f"clicked button")
                    else:
                        diagPrint (f"already clicked button")

            except TimeoutException:
                diagPrint("Timeout while locating button")
                success = False
            except NoSuchElementException:
                diagPrint("Unable to locate button")
                success = False
            except Exception as e:
                diagPrint (f"Error: Failed to toggle button {e}")
                success = False

        time.sleep(1)

        try:

            coinflip = random.uniform(0, 1)
            
            if coinflip >= commentProb:
                diagPrint("skipping comments")

            if success and coinflip < commentProb:

                if (thumb_pref < 0):
                    comment = random.choice(dislikelist)
                else:
                    comment = random.choice(likelist)

                streamer = self._channel.find_element_by_css_selector('textarea[id=comment]').clear()
                streamer = self._channel.find_element_by_css_selector('textarea[id=comment]').send_keys(comment)
                self._channel.find_element_by_css_selector('span[id=saveCommentBtn]').click()
                # debug
                diagPrint (f"input comment: {comment}")

        except Exception as e:
            diagPrint (f"Error: Failed to submit comment {e}")
            success = False

        return success






    # Upload benign video
    def sendMsgGood (self, destContext):

        if random.randint(1,50) != 1:
            return


        diagPrint (f"In Avideo sendMsgGOOD:")
        
        coverlist = ['Bird.mp4', 'Worship.mp4', 'Cheetah.mp4', 'Nebula.mp4', 'Plexus.mp4', 'Annapurna.mp4']

#            'crows1_130_norm.mp4', 'crows2_130_norm.mp4', 'jpshibuya_130_norm.mp4',
#                     'osaka1_130_norm.mp4', 'osaka3_130_norm.mp4', 'osaka4_130_norm.mp4',
#                     'yubatake1_130_norm.mp4', 'yubatake2_130_norm.mp4', 'yubatake3_130_norm.mp4',
#                     'yubatake4_130_norm.mp4', 'yubatake5_130_norm.mp4']
            
        coverfile = '/ramfs/destiniAvideo/covers/videos/' + coverlist[random.randrange(len(coverlist))] # random.choice(coverlist)

        good_file_path = tempfile.mktemp (suffix = '.mp4', dir = '/tmp')
        proc_stat = subprocess.run (['/usr/local/lib/race/comms/DestiniAvideo/scripts/trim.sh', coverfile, good_file_path], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        diagPrint (f'trim return code: {proc_stat.returncode} {good_file_path}')
        
        diagPrint (f"upload_filepath = {good_file_path}")


        _pTag  = str(datetime.now())


        diagPrint (f"HERE>>>HELLO1")


        # adding 'g' to ensure the set of tags for benign and steg videos are different
        _dynTags = DynamicTags.dynamicTagsFor (_pTag, 1, 2)
        tags     = _dynTags.tags()

        diagPrint (f"HERE>>>HELLO2")
        
        tags     = ' '.join(tags)

        encoder_url = self.wbInstance.get('encoder_url')
        _loop_count = 2

        diagPrint (f"HERE>>>HELLO3")
        
        while _loop_count:     # "do once" loop that permits graceful exit
            try:
                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Avideo:sendMsg (): detected closed channel")
                        break

                    self._channel.get (encoder_url)
                except Exception as e:
                    diagPrint (f"Error getting encoder url: {e} {encoder_url}")
                    raise

                diagPrint("In Avideo SendGOODMSG: 1")
                
                element = wait_catch_exception (self._channel, max_sleep,
                                                By.CSS_SELECTOR, "button[type=submit]",
                                                "Explicit wait error or submit")

                if (element == None):
                    diagPrint ("Avideo:sendMsg (): error waiting for encoder url")
                    diagPrint (f"Page Source = {self._channel.page_source}")
                    raise Exception ("Error waiting for encoderurl")

                             
                diagPrint(f"In Avideo SendGOODMSG: 2: {_pTag} {tags} {coverfile} {good_file_path}")
                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Avideo:sendMsg (): detected closed channel")
                        break
 
                     #html_source = self._channel.page_source                   
                     #with open('page.html', 'w') as f:
                     #    f.write(safe_str(html_source))


                    diagPrint("In Avideo SendGOODMSG: 3")
                    self._channel.find_element_by_css_selector('input[id=title]').send_keys(DynamicPhrases.getRandomPhrase())
                    self._channel.find_element_by_css_selector('textarea[id=description]').send_keys(tags)
                    time.sleep(0.5)
                    self._channel.find_element_by_css_selector('input[type=file]').send_keys(good_file_path)
                    time.sleep(0.5)
                                        
                    element = wait_catch_exception (self._channel, max_sleep, By.CSS_SELECTOR, "button[type=submit]",
                                                    "Explicit wait error for login/submit")
                    if (element == None):
                        raise

                    self._channel.find_element_by_css_selector('button[type=submit]').click()
                    time.sleep(2)
                    diagPrint("In Avideo SendGOODMSG: 4")

                    
                except:
                    diagPrint (f"A video encoder failed: {sys.exc_info ()[0]}")
                    raise

                if self._channel is None:   # accommodate the channel being asynchronously closed
                    diagPrint ("Avideo:sendMsg (): detected closed channel")
                    break

                diagPrint("In Avideo SendGOODMSG 5: Terminating do once loop")
                result = True
                time.sleep (5)
                break       # terminate the "do once" loop
            
            except Exception as e:
                _loop_count -= 1

                if _loop_count:
                    diagPrint (f"Re-establishing connection: {e}")
                    self._closeChannel ()
                    self._channel = self._openDriver ()
                                    
        return result    # return status
