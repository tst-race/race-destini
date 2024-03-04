import io
import os
import random
import subprocess
import sys
import tempfile
import hashlib
from threading import Thread, Condition, RLock
import time
from essential_generators import DocumentGenerator
from urllib.parse import quote

import requests
from urllib3.exceptions import InsecureRequestWarning

from bs4 import BeautifulSoup
from selenium import webdriver
from seleniumrequests import Firefox
from selenium.webdriver.firefox.options import Options
# for explicit wait
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from AbsWhiteboard import AbsWhiteboard
from DiagPrint import diagPrint
from DynamicTags import DynamicTags


# max sleep interval for explicit wait calls
max_sleep = 15


# Per Steven, disable warnings for unverified https
# https://stackoverflow.com/questions/27981545/suppress-insecurerequestwarning-unverified-https-request-is-being-made-in-pytho

requests.packages.urllib3.disable_warnings (category = InsecureRequestWarning)


os.system ('ps aux | grep geckodriver | grep -v grep | awk \'{print $2}\' | xargs kill -9 > /tmp/gecko.log   2>&1')
os.system ('ps aux | grep firefox     | grep -v grep | awk \'{print $2}\' | xargs kill -9 > /tmp/firefox.log 2>&1')




def safe_str(obj):
    return obj.encode('ascii', 'ignore').decode('ascii')


def wait_catch_exception(driver, wait_time, selector_type, selector, msg):
    element = None

    try:
        #diagPrint (f"in wait catch exception {wait_time}")
        element = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((selector_type, selector)))
        #diagPrint (f"done with webdriver wait {msg}")
    except TimeoutException:
        diagPrint (f"Timeout Exception: {msg}")
    except:
        diagPrint (f"Other Exception: {msg}, {sys.exc_info ()[0]}")
    
    return element


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

        self.min_num_tags   = wbCConfig.get ('min_num_tags', self._DEFAULT_MIN_NUM_TAGS)
        self.max_num_tags   = wbCConfig.get ('max_num_tags', self._DEFAULT_MAX_NUM_TAGS)

        self.dynTagsBrdcst  = []
        self.dynTagsPulling = None
        self.doc_gen = DocumentGenerator()

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


    # Use credentials, wbInstance, and wbCConfig maps to open and return a channel.
    #
    # user           # 'Bob Evans'
    # credentials    # {'account': 'BobEvans', 'password': '@bob_evans312'}
    # userContext    # {'tags': {'common': ['#washington', '#wdc'],
    #                            'pushing': ['#monument', '#senate'],
    #                            'pulling': ['#scotus', '#omb']
    #                           }
    # wbInstance     # {'class': 'Pixelfed', 'url': 'https://race.example2'}
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
        wb_url         = wbInstance.get ('url', None)
        wb_credentials = credentials if credentials else wbInstance.get ('credentials', None) 
        wb_driver_path = wbCConfig.get  ('driver_path', None)

        diagPrint(f"In Pixelfed openChannel {wb_class} {wb_url} {wb_driver_path} {wb_credentials}")

        if (wb_class != 'Pixelfed') or (wb_url == None) or (wb_driver_path == None):
            diagPrint(f"Pixelfed open channel failed... {wb_class} {wb_url}")
            return None

        wb_email = wb_credentials.get ('account',  None)
        wb_pass  = wb_credentials.get ('password', None)

        if (wb_email == None or wb_pass == None):
            diagPrint(f"Pixelfed login failed... bad credentials {wb_email} {wb_pass}")
            return None

        diagPrint("Pixelfed open channel HERE 1")

        ##############################
        # webdriver setup
        firefox_options = Options()
        firefox_options.headless = True

        diagPrint("Pixelfed open channel HERE 1.1")

        try:
            diagPrint("Pixelfed open channel HERE 1.2")
            firefox_profile = webdriver.FirefoxProfile()
            firefox_profile.set_preference("network.prefetch-next", False)
            firefox_profile.set_preference("accept_untrusted_certs", True)

            diagPrint("Pixelfed open channel HERE 1.3")
            driver = webdriver.Firefox(options=firefox_options, firefox_profile=firefox_profile, executable_path=wb_driver_path)
            driver.implicitly_wait (10) # sec
            driver.set_page_load_timeout (30)

            diagPrint("Pixelfed open channel HERE 1.4")

            # pixelfed login
            login_url = os.path.join (wb_url, 'login')
            num_tries = 5
            
            diagPrint("Pixelfed open channel HERE 1.5")
            
            while num_tries > 0:
                diagPrint("Pixelfed open channel HERE 2")

                try:
                    driver.get (login_url)
                    driver.find_element_by_css_selector ('input[type=email]')   .send_keys (wb_email)
                    driver.find_element_by_css_selector ('input[type=password]').send_keys (wb_pass)
                except Exception as e:
                    num_tries = num_tries - 1
                    if Whiteboard.WB_STATUS or Whiteboard.WB_STATUS_CHANGE_TIME == 0:
                        Whiteboard.WB_STATUS_CHANGE_TIME = time.time ()
                    Whiteboard.WB_STATUS = False
                    diagPrint (f"Exception error 2.1: {sys.exc_info ()[0]} {e}")
                    html_source = safe_str(driver.page_source)
                    diagPrint(f"{html_source}")
                    time.sleep(10)
                    continue

                element = wait_catch_exception (driver, max_sleep, By.CSS_SELECTOR, "button[type=submit]",
                                                "Explicit wait error for login/submit")

                if not Whiteboard.WB_STATUS:
                    Whiteboard.WB_STATUS = True
                    Whiteboard.WB_STATUS_CHANGE_TIME = time.time()

                if element:
                    break

                num_tries = num_tries - 1
                time.sleep(10)

        except Exception as e:
            diagPrint (f"Exception error 1: {sys.exc_info ()[0]} {e}")
            return None

        num_tries = 5
        diagPrint("Pixelfed open channel HERE 3.1")
            
        while num_tries > 0:
            try:
                driver.find_element_by_css_selector ('button[type=submit]').click ()
            except Exception as e:
                diagPrint (f"Exception error 3.2: {sys.exc_info ()[0]} {e}")

            element = wait_catch_exception (driver, max_sleep, By.CSS_SELECTOR, ".loggedIn",
                                            "Unexplained login failure")
            if element != None:
                diagPrint ("Logged into pixelfed")
                return driver

            num_tries -= 1
            time.sleep(10)
                
        diagPrint (f"ERROR: Logging into pixelfed.. {wb_url} returning None")
        return None

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
                                




    # Wait for and return inbound message 

    def recvMsg (self, userContext):

        def _pnmRunnable (_pipe, _pImage):

            # We specifically do _not_ use communicate (), which only
            # works with single processes because it hijacks stdout.

            _pipe.stdin.write (_pImage)
            _pipe.stdin.close ()        # Issue EOF
        
        # Employ recMsg queue; run selenium poller in thread

        if self.recvThread is None:
            _t_name = 'Pixelfed-recvMsg-{}'.format (self.user)
            self.recvThread = self.startThread (_t_name, self._recvMsg, (userContext, ))

        while self._channel:    # accommodate the channel being asynchronously closed
            with self.recvLock:
                if self.recvQueue:
                    _imgIn = self.recvQueue.pop (0)

                    diagPrint (f'popping 1... input: {len (_imgIn)}')

                    #if not True:
                    return _imgIn

                
                    
                    # https://stackoverflow.com/questions/13332268/how-to-use-subprocess-command-with-pipes

                    # _toPNM     = subprocess.Popen (('jpegtopnm', ), stdin = subprocess.PIPE, stdout = subprocess.PIPE)
                    # _pnmThread = Thread (target = _pnmRunnable, name = 'PNM Thread', args = (_toPNM, _imgIn))
                    # _toJPEG    = subprocess.Popen (('ppmtojpeg', '-quality', '45'), stdin = _toPNM.stdout, stdout = subprocess.PIPE)
                    # _pnmThread.start ()
                    # _toPNM.stdout.close ()

                    # diagPrint ("popping 2... gathering stdout")

                    # _pieces = bytearray ()

                    # while True:
                    #     retcode = _toJPEG.poll ()
                    #     if retcode is None:
                    #         _piece = _toJPEG.stdout.read ()
                    #         if _piece:
                    #             _pieces += _piece
                    #     else:
                    #         diagPrint (f'poll () returned {retcode}')
                    #         break

                    # _imgOut = bytes (_pieces)

                    # if len (_imgOut) != 0:
                    #     return _imgOut
                else:
                    self.recvLock.wait ()

        return None

    def pixelfed_feedback (self):

        success = True
        likelist = ['nice shot', 'terrific', 'awesome', 'very good', 'excellent', 'amazing', 'magnificent', '2 thumbs up!', 'wonderful', 'wow!!', 'super', 'like it', 'thumbs up', 'good', 'stellar', 'Wonderful', 'Good!', 'cool', 'Cool!', 'like it', 'I like it', 'very original', 'nice scenary', 'wish I could be there', 'where is this?', 'what place is this?', 'clever', 'curious', 'never been there', 'been there, done that', 'recommended', 'highly recommend', 'more like this', 'sweet', 'fantastic', 'natural', 'love nature', 'so blue', 'so pretty', 'fantasatic!', 'love it', 'perfect', 'my favorite', 'Where is this and when can we eat it together?', 'You make everything look so fun!', 'Photo credit for this amazing pic', 'Your life is like a movie, and I just need some popcorn.', 'Excuse me, sunset, but you are in the way of looking at my beautiful bestie.', 'How did I get so lucky to have such a cool best friend?', 'Can we get brunch again this weekend?', 'We shore do know how to seas the day.', 'LOL', 'can I have this picture framed?', 'Frame That!']

        dislikelist = ['boring', 'ok', 'blah blah blah', 'really?', 'bad idea', 'disgusting', 'poor shot', 'weird', 'awful', 'blah', 'too blurry', 'sad', 'poor', 'so bad', 'this is so bad', 'awful', 'terrible pic', 'bad shot', 'dont like this one', 'not my favorite']

        commentProb = self.wbInstance.get ('comment_prob', 0.1)
        search_tag = ""
        thumb_pref = random.randint(0,2)

        diagPrint(f"In pixelfed feedback")

        # construct a search url based on input search_tag, if specified

        if search_tag == "":
            search_url = os.path.join (self.wbInstance.get ('url'), 'discover')
        else:
            search_url_base = os.path.join (self.wbInstance.get ('url'), 'discover/tags/')
            search_url = search_url_base + quote(search_tag)

        diagPrint (f"search_url: {search_url}")

        try:
            self._channel.get(search_url)
            # find an image url 
            time.sleep(1)

        except Exception as e:
            diagPrint (f"Error: driver.get failed {e}")
            success = False



        html_source = safe_str(self._channel.page_source)
        with open('search.html', 'w') as f:
            f.write(html_source)

        try:  
            soup = BeautifulSoup(html_source, features="html.parser")
            match = soup.find("a", class_="info-overlay")

            # no images were found
            if match is None:
                return False

            img_url = match.get('href')
            if img_url:
                #diagPrint (f"{img_url}")
                # img_url.click()
                diagPrint (f"found img url")
            else:
                diagPrint (f"img url not found")
        except TimeoutException:
            diagPrint("Timeout while locating like button")
            success = False
        except NoSuchElementException:
            diagPrint("Unable to locate img link")
            success = False
        except Exception as e:
            diagPrint (f"Error: Failed to find and click img link {e}; possibly no match for tag")
            success = False


        if success:
            try:
                self._channel.get(img_url)

                # visit the image url 
                time.sleep(1)

                html_source = safe_str(self._channel.page_source)
                with open('imglink.html', 'w') as f:
                    f.write(html_source)

            except Exception as e:
                diagPrint (f"Error: driver.get failed {e}")
                success = False


        # click the thumbs-up button, if specified

        html_source_thumbup = safe_str(self._channel.page_source)
        with open('thumbup.html', 'w') as f:
            f.write(html_source_thumbup)

        if success and (thumb_pref > 0):

            diagPrint ("inside thumb_pref")

            try:
                soup = BeautifulSoup(html_source_thumbup, features="html.parser")
                heart = soup.find("h3", class_="like-btn")

                if heart:
                    diagPrint (f"like-btn found")
                    thumbButton = self._channel.find_element_by_css_selector('h3[title=Like]')
                    if thumbButton:
                        thumbButton.click()
                        time.sleep(1)
                        diagPrint (f"clicked like button")
                    else:
                        diagPrint (f"cannot find like button")
                else:
                    diagPrint (f"like-btn not found; already liked?")

            except TimeoutException:
                diagPrint("Timeout while locating like button")
                success = False
            except NoSuchElementException:
                diagPrint("Unable to locate like button")
                success = False
            except Exception as e:
                diagPrint (f"Error: Failed to click like button {e}")
                success = False

        else:
            if not success:
                diagPrint ("success false")
            if thumb_pref <= 0:
                diagPrint ("no thumbs up specified")



        # input comment, based on coin flipping result 

        try:
            # if success and (comment != ""):
            coinflip = random.uniform(0, 1)
            if coinflip >= commentProb:
                diagPrint ("skipping comments")

            if success and coinflip < commentProb:

                if (thumb_pref < 0):
                    comment = random.choice(dislikelist)
                else:
                    comment = random.choice(likelist)

                streamer = self._channel.find_element_by_css_selector('textarea[name=comment]').clear()
                streamer = self._channel.find_element_by_css_selector('textarea[name=comment]').send_keys(comment)
                # driver.find_element_by_css_selector('span[id=saveCommentBtn]').click()
                # debug
                diagPrint (f"input comment: {comment}")

                postBtn = self._channel.find_element_by_css_selector('input[value=Post]')
                if postBtn:
                    postBtn.click()
                    time.sleep(1)
                    diagPrint (f"clicked post button")
                else:
                    diagPrint (f"failed to find and click post button")


        except Exception as e:
            diagPrint (f"Error: Failed to submit comment {e}")
            success = False

        return success



    def _recvMsg (self, userContext):
        try:
            self._recvMsgPriv (userContext)
        except Exception as e:
            diagPrint (f"Error in recvMsgPriv {e}" )

    def _recvMsgPriv (self, userContext):

        if self._channel is None or isinstance (self._channel, bool):
            self._channel = self._openDriver()
            
        loop_delay = self.wbInstance.get ('loop_delay', 1)
        prev_count = 0

        # Poll for forever or until the channel is closed

        while self._channel:    # accommodate the channel being asynchronously closed
            diagPrint (f"looping inside PixelfedSelenium:_recvMsgPriv")

            # Search last three tag intervals, starting with "now".
            self.inactive_count = self.inactive_count + 1
            bDynTags = []
            for _dynTagBrdcst in self.dynTagsBrdcst:
                bDynTags.extend (list (map (_dynTagBrdcst.words, [0, -1])))
            pDynTags = list (map (self.dynTagsPulling.words, [0, -1]))

            dynTags = bDynTags
            dynTags.extend (pDynTags)

            for search_tags in dynTags:
                # Search for time-based dynamic word (viz., tag without leading '#')
                # Note: we're not using tags in 'common'
                search_tag      = search_tags[random.randrange (len (search_tags))]
                search_url_base = os.path.join (self.wbInstance.get ('url'), 'discover/tags/')
                search_url      = search_url_base + quote (search_tag)
                diagPrint (f"Pixelfed: _recvMsg: searching tag = {search_tag}")

                while True:         # "do once" loop that permits early exits
                    try:
                        self.setTimer ('searchURL')
                        self._channel.get (search_url)
                    except:
                        self.incrementStatus ('searchURLError')
                        diagPrint (f"Exception error 2: {sys.exc_info ()[0]}.  Setting Whiteboard Status to False")
                        if Whiteboard.WB_STATUS or Whiteboard.WB_STATUS_CHANGE_TIME == 0:
                            Whiteboard.WB_STATUS_CHANGE_TIME = time.time()                        
                        Whiteboard.WB_STATUS = False

                        self._closeChannel ()
                        self._channel = None

                        while self._channel == None:
                            time.sleep (15)
                            self._channel = self._openDriver()
                        break               # TBD: is this a pathological failure?
                    finally:
                        self.setTimer ('searchURL', False)

                    #wait_discover = "/api/v2/discover/tag?hashtag=" + search_tag + "&page=1"
                    #self._channel.wait_for_request (wait_discover)

                    if not Whiteboard.WB_STATUS:
                        Whiteboard.WB_STATUS = True
                        Whiteboard.WB_STATUS_CHANGE_TIME = time.time()

                    if self.inactive_count > 300:
                        time.sleep(random.randrange(6)+1)
                    else:
                        time.sleep(random.randrange(3)+1)

                    html_source = self._channel.page_source

                    ##############################
                    # extracting urls for the matches
                    soup = BeautifulSoup (html_source, features = "html.parser")

                    matches    = soup.find ('body', class_ = 'loggedIn')

                    if matches is None or len (matches) == 0:
                        diagPrint ("ERROR: Pixelfed recvMsg: Not Logged In")
                        break

                    image_urls      = []
                    matches         = soup.find_all ('div', class_ = 'square-content')                
                    pseudo_hrefs    = soup.find_all ('a', class_ = 'card info-overlay card-md-border-0')
                    count           = len (matches) if matches else 0

                    diagPrint(f"searching for tag = {search_tag}") 
                    if count != prev_count: 
                        diagPrint (f'count = {count}')
                        prev_count = count

                    match_sofar = 0

                    diagPrint(f"count = {count}")

                    if count <= 0:
                        diagPrint(f"breaking from while")
                        break

                    else:

                      if pseudo_hrefs is None:
                          diagPrint(f'Pseudo is None; count= {count}')
                          break

                      diagPrint(f'Pseudo: {len(pseudo_hrefs)}  {count}')

                      if matches is None:
                          matches = []

                      for match in matches:

                          # hack: derive the url for the image based upon the thumbnail's
                          ##############################
                          # TBD: fetch other pages if the 1st page doesn't contain all results

                          if pseudo_hrefs is not None and len (pseudo_hrefs) <= match_sofar:
                              diagPrint (f'pseudo_hrefs len mismatch: this should not happen')
                              break


                          pseudo_href = pseudo_hrefs[match_sofar].get('href')
                          #diagPrint(f'type of pseudo_href element = {type(pseudo_href)}')
                          #pseudo_href = pseudo_href.get('href')
                          #diagPrint(f'type of pseudo_href = {type(pseudo_href)}')
                          #diagPrint(f'type of match = {type(match)}')
                          match_sofar = match_sofar + 1
                          match_style = match.get ('style')
                          segments    = match_style.split ('"')

                          if (len (segments) == 3):
                             thumb_url = segments[1]
                             image_url = thumb_url.replace ("_thumb", "")
                             #diagPrint (f'{image_url}')

                             if (not self._url_cache.isCached (image_url)
                                 and not self._url_cache.isCached(pseudo_href)):

                                 # weird selenium failure case...with truncated image url
                                 # so now get the url from pseudo_hrefs and follow through
                                 if ("jpeg" not in image_url): 
                                     try:
                                         self._channel.get(pseudo_href)
                                         thumb_html_source = self._channel.page_source
                                         soup2 = BeautifulSoup (thumb_html_source, features = "html.parser")
                                         match_og    = soup2.find (property = "og:image")
                                         thumb_url = match_og.get('content')
                                         image_url = thumb_url.replace ("_thumb", "")
                                         diagPrint (f"PseudoURL: {image_url}")

                                         # third attempt....
                                         if "jpeg" not in image_url:
                                             diagPrint (f"PseudoHREF with non jpeg in og:image: {pseudo_href}")
                                             elem = self._channel.find_element_by_class_name('null.card-img-top');
                                             image_url = elem.get_attribute('src')
                                             diagPrint (f"IMAGE URL: {image_url}")


                                         if "jpeg" in image_url:
                                             self._url_cache.cache(pseudo_href)
                                         else:
                                             self.incrementStatus ('noImageURLError')
                                             diagPrint(f"Still no image URL after 3 tries!!!")

                                     except:
                                         diagPrint (f"Exception error 3: {sys.exc_info ()[0]}")
                                         break;

                                 if "jpeg" in image_url:
                                     image_urls.append (image_url)
                                     diagPrint (f"{image_url}")
                                 else:
                                     diagPrint(f"not adding {image_url}")

                    self._url_cache.checkCache ()

                    if image_urls:

                        ##############################
                        # selenium doesn't seem to support one to download a file (e.g., jpeg file) directly
                        #
                        # we construct a get request (need to import requests) with the user-agent string
                        # and cookie used by selenium

                        # find the cookies used by selenium
                        try:
                            selenium_cookies = self._channel.get_cookies ()
                        except:
                            self.incrementStatus ('getCookiesError')
                            diagPrint (f"Exception error 4: couldn't get cookies; {sys.exc_info ()[0]}")
                            break           # TBD: is this a pathological failure?

                        cookies = {
                            'value': selenium_cookies[0].get ('value'),
                        }

                        try: 
                            # find the user-agent string used by selenium
                            user_agent = self._channel.execute_script ("return navigator.userAgent;")
                        except:
                            self.incrementStatus ('getUserAgentError')
                            diagPrint (f"Exception error 5: couldn't get useragent; {sys.exc_info ()[0]}")
                            break           # TBD: is this a pathological failure?

                        headers = {
                            'User-Agent': user_agent,
                        }

                        for url in image_urls:
                            try:
                                self.setTimer ('getImage')
                                # turn-off cert verification, because our pixelfed uses
                                # a self-signed cert
                                # TBD: will this be true for _all_ Pixelfed installations?
                                # Should we add this to the JSON?
                                response = requests.get (url, cookies = cookies, headers = headers, verify = False)
                                image_download = response.content
                                self.inactive_count = 0

                                                        

                                with self.recvLock:
                                    self._url_cache.cache(url)
                                    self.recvQueue.append (image_download)
                                    self.recvLock.notify ()
                            except:
                                self.incrementStatus ('getImageError')
                                diagPrint (f"Exception error 6: url fetch failed; {sys.exc_info ()[0]}")
                            finally:
                                self.setTimer ('getImage', False)

                    break           # "do once"

    #            del self._channel.requests

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


                
            # call pixelfed feedback once in 50 times 
            if (random.randint(1,50) > 49):
                diagPrint(f"calling pixelfed_feedback")        
                self.pixelfed_feedback()

    def getMaxSendMsgCount(self):
        return 1


    
    # Send a message.  Return True if successful, False if retry.

    def sendMsg (self, destContext, msgList):
        with Whiteboard._PusherMutex:
            return self._sendMsgMutex (destContext, msgList)

    def _sendMsgMutex (self, destContext, msgList):

        if Whiteboard._PusherDriver is None:
            Whiteboard._PusherDriver = self._openDriver()

        self._channel = Whiteboard._PusherDriver
        
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

        for msg in msgList:
            fd, stego_path = tempfile.mkstemp (suffix = '.jpg', dir = '/tmp', text = False)
            os.write (fd, msg)
            os.close (fd)
            image_bytes = image_bytes + len (msg)
            
            if steg_file_list != '':
                steg_file_list = steg_file_list + '\n' + stego_path
            else:
                steg_file_list = stego_path
                
        diagPrint (f"steg_file_list = {steg_file_list}" )

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

        cnt = random.randint(1,10) % 2

        while (cnt > 0):
            tags.append ('#' + self.doc_gen.word())
            cnt = cnt - 1

        random.shuffle(tags)
        tags = ' '.join(tags)


        composeurl  = os.path.join (self.wbInstance.get ('url'), 'i/compose')
        _loop_count = 2
        
        while _loop_count:     # "do once" loop that permits graceful exit
            try:
                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Pixelfed:sendMsg (): detected closed channel")
                        break

                    self.setTimer ('getURL')
                    self._channel.get (composeurl)
                    self.setTimer ('getURL', False)
                except Exception as e:
                    diagPrint (f"Error getting compose url: {e} {composeurl}")
                    raise

                self.setTimer ('waitCaption')
                element = wait_catch_exception (self._channel, max_sleep, By.XPATH,
                                                "//div[@class=\'caption\']/textarea",
                                                "Explicit wait error for caption")
                self.setTimer ('waitCaption', False)
                if (element == None):
                    self.incrementStatus ('waitCaptionError')
                    diagPrint ("Pixelfed:sendMsg (): error waiting for caption")
                    diagPrint (f"Page Source = {self._channel.page_source}")
                    diagPrint ("done printing page source")
                    raise Exception ("Error waiting for caption")

                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Pixelfed:sendMsg (): detected closed channel")
                        break

                    self.setTimer ('addTags')

                    # fill in the caption field with tags
                    caption = self._channel.find_element_by_xpath ("//div[@class=\'caption\']/textarea")
                    caption.clear ()

                    # diagPrint(f'calling send_key tags {caption}')
                    caption.send_keys (tags)
                    # diagPrint('returning from send_key tags')

                    self.setTimer ('addTags', False)
                except:
                    self.incrementStatus ('addTagsError')
                    diagPrint (f"Exception error 7: {sys.exc_info ()[0]}")
                    raise

                self.setTimer ('waitAccept')
                element = wait_catch_exception (self._channel, max_sleep, By.XPATH,
                                                "//input[@accept='image/jpeg,image/png,image/gif']",
                                                "Explicit wait error for accept")
                self.setTimer ('waitAccept', False)
                if (element == None):
                    self.incrementStatus ('waitAcceptError')
                    diagPrint ("Pixelfed:sendMsg (): error waiting for accept")
                    raise Exception ("Error waiting for accept")

                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Pixelfed:sendMsg (): detected closed channel")
                        break

                    # send the absolute path of the file to be uploaded to the "hidden" element
                    self.setTimer ('sendPath')
                    image = self._channel.find_element_by_xpath ("//input[@accept='image/jpeg,image/png,image/gif']")

                    diagPrint(f"calling send_keys {steg_file_list} {image.text}")
                    image.send_keys (steg_file_list)

                    # diagPrint(f"returning send_keys {steg_file_list}")
                    
                    # this does not work without selenium wire
                    #self._channel.wait_for_request ('/api/pixelfed/v1/media')
                    time.sleep(1)
                                        
                    self.setTimer ('sendPath', False)
                except:
                    self.incrementStatus ('sendPathError')
                    diagPrint (f"Exception error 8: {sys.exc_info ()[0]}")
                    raise

                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Pixelfed:sendMsg (): detected closed channel")
                        break

                    self.setTimer ('findPublish')

                    # EC.presence_of_element_located((By.XPATH, "//div[@class='pl-md-5']"))
                    element = WebDriverWait (self._channel, max_sleep).until (
                        EC.element_to_be_clickable ((By.XPATH, "//div[@class='pl-md-5']"))
                    )
                except TimeoutException:
                    self.incrementStatus ('findPublishTimeout')
                    diagPrint ("Timeout while locating locate the publish button")
                    raise
                except NoSuchElementException:
                    self.incrementStatus ('findPublishNotFound')
                    diagPrint ("Unable to locate the publish button")
                    raise
                finally:
                    self.setTimer ('findPublish', False)

                try:
                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Pixelfed:sendMsg (): detected closed channel")
                        break

                    self.setTimer ('uploadImage')
                    #                time.sleep (1)

                    # diagPrint("finding element by xpath")
                    publish = self._channel.find_element_by_xpath ("//div[@class='pl-md-5']")
                    # diagPrint("calling publish.click")
                    publish.click ()
                    diagPrint (f"Pixelfed: Uploading Image with {tags}")
                except:
                    diagPrint (f"Exception error 9: {sys.exc_info ()[0]}")
                    raise
                finally:
                    self.setTimer ('uploadImage', False)

                if self._channel is None:   # accommodate the channel being asynchronously closed
                    diagPrint ("Pixelfed:sendMsg (): detected closed channel")
                    break

                click_counter = 0

                while click_counter < 3:
                    self.setTimer ('findClassCount')
                    element = wait_catch_exception (self._channel, 5, By.XPATH,
                                                "//span[@class='like-count']",
                                                "Error locating class like-count ")
                    self.setTimer ('findClassCount', False)
                    
                    if element != None:
                        break;

                    self.incrementStatus ('findClassCountError')                    
                    diagPrint ("Pixelfed:sendMsg (): error locating class like-count..")

                    click_counter = click_counter + 1
                    
                    if click_counter == 3:                        
                        diagPrint (f"{self._channel.page_source}")
                        raise Exception ("error locating class like-count")
                    
                    diagPrint ("retrying...")
                    publish = self._channel.find_element_by_xpath ("//div[@class='pl-md-5']")
                    publish.click ()

                    if self._channel is None:   # accommodate the channel being asynchronously closed
                        diagPrint ("Pixelfed:sendMsg (): detected closed channel")
                        break

                try:
                    # check to see if the page's title starts with "A post by ", indicating the upload succeeds
                    afterclick_page = self._channel.page_source
                    soup_afterclick = BeautifulSoup (afterclick_page, features = "html.parser")
                    og_title_ref    = soup_afterclick.find ("meta", property = "og:title")
                    og_title        = og_title_ref["content"]
                    
                    if not og_title.startswith ('A post by '):
                        self.incrementStatus ('possibleUploadFailure')
                        diagPrint (f"Upload possibly failed.  og_title is {og_title}")
                    else:
                        diagPrint (f"Upload successful")
                        self.trackAdd (nItems = len(msgList), nBytes = image_bytes)
                        result = True
                except Exception as e:
                    diagPrint (f"Exception error 10: Some other upload exception in Pixelfed.py; {sys.exc_info ()[0]}")
                    diagPrint (f"{e}")
                    raise

                break       # terminate the "do once" loop
            
            except Exception as e:
                _loop_count -= 1

                if _loop_count:
                    if  "loggedIn" not in safe_str(self._channel.page_source):
                        diagPrint (f"Re-establishing connection {e}")
                        self._closeChannel ()
                        Whiteboard._PusherDriver = self._openDriver ()
                        self._channel = Whiteboard._PusherDriver
                    else:
                        time.sleep(5)
                
        os.remove (stego_path)

        #del self._channel.requests

        return result    # return status





    # def uploadBenignImage (self):

    #     tag = "benign"
    #     composeurl  = os.path.join (self.wbInstance.get ('url'), 'i/compose')
    #     _loop_count = 2
        
    #     while _loop_count:     # "do once" loop that permits graceful exit
    #         try:
    #             try:
    #                 if self._channel is None:   # accommodate the channel being asynchronously closed
    #                     diagPrint ("Pixelfed:uploadBenignImage (): detected closed channel")
    #                     break
    #                 self._channel.get (composeurl)
    #             except Exception as e:
    #                 diagPrint (f"Error getting compose url: {e} {composeurl}")

    #             element = wait_catch_exception (self._channel, max_sleep, By.XPATH,
    #                                             "//div[@class=\'caption\']/textarea",
    #                                             "Explicit wait error for caption")

    #             if (element == None):
    #                 diagPrint ("Pixelfed:uploadBenignImage (): error waiting for caption")
    #                 diagPrint (f"Page Source = {self._channel.page_source}")
    #                 raise Exception ("Error waiting for caption")

    #             try:
    #                 if self._channel is None:   # accommodate the channel being asynchronously closed
    #                     diagPrint ("Pixelfed:uploadBenignImage (): detected closed channel")
    #                     break

    #                 # fill in the caption field with tags
    #                 caption = self._channel.find_element_by_xpath ("//div[@class=\'caption\']/textarea")
    #                 caption.clear ()
    #                 caption.send_keys (tags)

    #             except:
    #                 diagPrint (f"Exception error 7: {sys.exc_info ()[0]}")

    #             element = wait_catch_exception (self._channel, max_sleep, By.XPATH,
    #                                             "//input[@accept='image/jpeg,image/png,image/gif']",
    #                                             "Explicit wait error for accept")

    #             if (element == None):
    #                 self.incrementStatus ('waitAcceptError')
    #                 diagPrint ("Pixelfed:sendMsg (): error waiting for accept")
    #                 raise Exception ("Error waiting for accept")

    #             try:
    #                 if self._channel is None:   # accommodate the channel being asynchronously closed
    #                     diagPrint ("Pixelfed:sendMsg (): detected closed channel")
    #                     break

    #                 # send the absolute path of the file to be uploaded to the "hidden" element
    #                 image = self._channel.find_element_by_xpath ("//input[@accept='image/jpeg,image/png,image/gif']")

    #                 random_file = 'abc' # pick random file from covers folder
    #                 diagPrint(f"calling send_keys {random_file} {image.text}")
    #                 image.send_keys (random_file)

    #                 # diagPrint(f"returning send_keys {steg_file_list}")
                    
    #                 # this does not work without selenium wire
    #                 #self._channel.wait_for_request ('/api/pixelfed/v1/media')
    #                 time.sleep(1)
                                        
    #             except:
    #                 diagPrint (f"Exception error 8: {sys.exc_info ()[0]}")

    #             try:
    #                 if self._channel is None:   # accommodate the channel being asynchronously closed
    #                     diagPrint ("Pixelfed:sendMsg (): detected closed channel")
    #                     break

    #                 self.setTimer ('findPublish')

    #                 # EC.presence_of_element_located((By.XPATH, "//div[@class='pl-md-5']"))
    #                 element = WebDriverWait (self._channel, max_sleep).until (
    #                     EC.element_to_be_clickable ((By.XPATH, "//div[@class='pl-md-5']"))
    #                 )
    #             except TimeoutException:
    #                 diagPrint ("Timeout while locating locate the publish button")
    #             except NoSuchElementException:
    #                 diagPrint ("Unable to locate the publish button")

    #             try:
    #                 if self._channel is None:   # accommodate the channel being asynchronously closed
    #                     diagPrint ("Pixelfed:sendMsg (): detected closed channel")
    #                     break

    #                 # diagPrint("finding element by xpath")
    #                 publish = self._channel.find_element_by_xpath ("//div[@class='pl-md-5']")
    #                 # diagPrint("calling publish.click")
    #                 publish.click ()
    #                 diagPrint (f"Pixelfed: Uploading Image with {tags}")
    #             except:
    #                 diagPrint (f"Exception error 9: {sys.exc_info ()[0]}")

    #             if self._channel is None:   # accommodate the channel being asynchronously closed
    #                 diagPrint ("Pixelfed:uploadBenignImage (): detected closed channel")
    #                 break

    #             element = wait_catch_exception (self._channel, 5, By.XPATH,
    #                                             "//span[@class='like-count']",
    #                                             "Error locating class like-count ")

    #             if (element == None):
    #                 self.incrementStatus ('findClassCountError')
    #                 diagPrint ("Pixelfed:uploadBenignImage (): error locating class like-count")
    #                 diagPrint (f"{self._channel.page_source}")
    #             try:
    #                 if self._channel is None:   # accommodate the channel being asynchronously closed
    #                     diagPrint ("Pixelfed:sendMsg (): detected closed channel")
    #                     break

    #                 # check to see if the page's title starts with "A post by ", indicating the upload succeeds
    #                 afterclick_page = self._channel.page_source
    #                 soup_afterclick = BeautifulSoup (afterclick_page, features = "html.parser")
    #                 og_title_ref    = soup_afterclick.find ("meta", property = "og:title")
    #                 og_title        = og_title_ref["content"]

    #                 if not og_title.startswith ('A post by '):
    #                     diagPrint (f"Upload possibly failed.  og_title is {og_title}")
    #                 else:
    #                     result = True

    #             except:
    #                 diagPrint (f"Exception error 10: Some other upload exception in Pixelfed.py; {sys.exc_info ()[0]}")

    #             break       # terminate the "do once" loop
            
    #         except Exception as e:
    #             _loop_count -= 1

    #             if _loop_count:
    #                 if  "loggedIn" not in safe_str(self._channel.page_source):
    #                     diagPrint (f"Re-establishing connection {e}")
    #                     self._closeChannel ()
    #                     self._openChannel ()
    #                 else:
    #                     time.sleep(5)
                
    #     os.remove (stego_path)
    #     return 

