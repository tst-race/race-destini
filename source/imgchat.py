import os
import sys
import json
import glob
import time
# import pywedge
import secrets
import datetime
from nullchat import *
from DynamicTags import *
from waiter import simpleWaiter
from commsPluginBindings import RaceLog

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


    def get_words(self):
        if self.nwords == 1:    # Sender side will ask for one word
            result = list( map(self.dt.words, [0]) )
        elif self.nwords == 3:  # Receiver will check 3
            result = list( map(self.dt.words, [0, -1, -2]) )
        return result
    

    def next_word(self):
        word = self.wlist[self.k]
        self.k += 1
        if self.k > len(self.wlist):
            self.k = 0
        return word
        



class ImgChat(NullChat):
    _USE_DYNAMIC_TAGS = False
    
    def __init__(self, tmpdir="/tmp/", dir=default_cover_dir, user='user1', reverse=False, verbose=False, authfile="./wbauth.json"):
        super().__init__(tmpdir, dir, user, reverse, verbose)
        self.covers = glob.glob(default_cover_dir+'*')
        self.titles = [ f"Image_{k}" for k in range(len(self.covers)) ]
        self.timestamps = [0 for i in range(len(self.covers))]
        self.wbname = "generic"

        # Interactive mode:
        self.sleep_range = (1,2)

        # These simpleWaiter objects offer a Poission-ish wait and
        # throttle for queries to the whiteboards.  The defaults
        # amount to about 1 post or query per second.  Most
        # whiteboards are more conservative and we deal with that by
        # setting different parameters for the waiters:
        
        # self.post_waiter = simpleWaiter(limit=3600, interval=3600, min_wait=1)
        # self.query_waiter = simpleWaiter(limit=3600, interval=3600, min_wait=1)
        
        #  self.setup_channels(tmpdir, reverse)
        
        # The JSON file used here is whiteboard-specific.  The imgchat
        # default is not terribly meaningful, so each chat class
        # overrides it to customize the auth flow for each whiteboard.
        # But here is where we load that JSON file:
        if authfile is not None:
            self.wb_auth = self.load_auth_file(authfile)


    def msg(self, string):
        if self.verbose:
            now = str(datetime.datetime.now())
            # print(f"[{now}]> {self.wbname}: {string}")
            RaceLog.logInfo("Destini", {self.wbname + ":" + string}, "")

            

    # Interactive sleep - this is currently called in interactive mode:
    def sleep(self):
        s = random.randrange(self.sleep_range[0], self.sleep_range[1])
        self.msg(f"  sleep {s} seconds.")
        time.sleep(s)

    def load_auth_file(self, filename="./wbauth.json", verbose=False):
        if not os.path.exists(filename):
            return None
        sl = []
        print(f"Loading authentication information from {filename}")
        with open(filename) as f:
            for raw in f:
                l = raw.split('//')[0][0:-1]
                if len(l) > 0:
                    sl = sl + [ l ]
                    if verbose:
                        print(l)
        json_in = ' '.join(sl)
        desc = json.loads(json_in)
        print(f"Done: {desc}")
        return desc


    def post_wait(self):
        x = self.post_waiter.compute_wait()
        self.msg(f" post_wait for {x} seconds")
        sys.stdout.flush()
        self.post_waiter.wait()
        self.msg(" post_wait done..")

    def query_wait(self):
        x = self.query_waiter.compute_wait()
        self.msg(f" query_wait for {x} seconds")
        sys.stdout.flush()
        self.query_waiter.wait()
        self.msg(" query_wait done.")

    def get_next_title(self, k):
        # Note that k starts at 1: Choose the tag source that we need
        # to use.  There are two: one inbound and one outbound:
        if k == 1:
            gen = self.recvgen
        else:
            gen = self.sendgen
        title = gen.get_words()
        self.msg(f"     Retrieving next title: {title}")
        return title


    def wait_for_response(self, which, max_iter=100, sleeptime=1):
        file = self.covers[which]
        last_update_time = self.timestamps[which]
        info = os.state(file)
        cur = into.st_mtime
        while cur <= last_update_time:
            sleep(sleeptime)
            info = os.state(file)
            cur = into.st_mtime
        return cur


    def setup_channels(self, tmpdir, reverse):
        DynamicTags.Initialize ('config/wordlist.txt', refresh=600)  # Refresh once every 10 minutes
        prefix = self.wbname
        self.choices = {}
        self.pid = os.getpid()
        # For now, we're going to have to use simple keys as the seed:
        
        if reverse:
            self.inbound = os.path.join(tmpdir, f"{prefix}_{self.pid}_o")
            self.outbound = os.path.join(tmpdir, f"{prefix}_{self.pid}_i")
            self.choices['inbound'] = 1
            self.choices['outbound'] = 2
            self.sendgen = WordGen('chan1', sender=True)
            self.recvgen = WordGen('chan2', sender=False)
        else:
            self.inbound = os.path.join(tmpdir, f"{prefix}_{self.pid}_i")
            self.outbound = os.path.join(tmpdir, f"{prefix}_{self.pid}_o")
            self.choices['inbound'] = 2
            self.choices['outbound'] = 1
            self.sendgen = WordGen('chan2', sender=True)
            self.recvgen = WordGen('chan1', sender=False)
            
        #title1 = self.get_next_title( self.choices['inbound'] )
        #title2 = self.get_next_title( self.choices['outbound'] )

        #print(f"{self.wbname} inbound title:  {title1}")
        #print(f"{self.wbname} outbound title: {title2}")
        
        #if self._USE_DYNAMIC_TAGS:
        #    self.titles[ self.choices['inbound'] ] = title1
        #    self.titles[ self.choices['outbound'] ] = title2


    def find_photo(self, title):
        return self.inbound

    def upload_photo(fileanme, title, description):
        return self.inbound

    def delete_photo(self, photo):
        return self.inbound

    def download_photo(self, photo):
        return self.inbound
    
    def write(self, string):
        cover = self.covers[0]
        try:
            pywedge.wedge_file(cover, string, self.outbound, logfile=None)
            return True
        except:
            return False


    def read(self):
        out = None
        if os.path.exists(self.inbound):
            b = pywedge.unwedge_file(self.inbound, 0, logfile=None)
            out = b.decode('UTF-8')
        return out

    def pump(self, image_in, image_out, title="Pump"):
        photo = self.find_photo(title)
        if photo is not None:
            self.delete_photo(photo)
        self.upload_photo(image_in, title, "Test")
        time.sleep(5)
        photo = self.find_photo(title)
        return self.download_photo(photo, image_out)

    # These are not whiteboard-specific, so we'll allow all
    # specialized chat objects to inherit these:


    def send(self, string, title=None):
        k = self.choices['outbound']
        choices = self.sendgen.get_words()
        if len(choices) > 1:
            print(f" Uh oh -- sender is getting too many titles: {choices}")
        title = choices[0]

        self.post_wait()
        result = self.write(string, title[0])
        while not result:
            self.post_wait()
            result = self.write(string, title[0])



    def receive(self):
        k = self.choices['inbound']
        out = None
        self.wait_for_update(k)
        choices = self.recvgen.get_words()
        for title in choices:
            self.query_wait()
            self.msg(f"   receive: Checking for title {title[0]}")
            out = self.read(title[0])
            if out is None:
                self.msg(f"   receive: Read returned nothing.")
            else:
                self.msg(f"   receive: Read returned {len(out)} bytes.")
                return out


    def gen_nonce(self):
        return secrets.token_urlsafe()
