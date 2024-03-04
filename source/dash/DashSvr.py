import json
import os
import random
import subprocess
import tempfile
from threading import Condition, Thread

from AbsWhiteboard import AbsWhiteboard
from IOManager import IOManager, IOM_MT_D_SVR, IOM_CT_GENERAL
from DiagPrint import diagPrint


class _AbsMediaPath (object):

    def __init__ (self):
        super ().__init__ ()

        self._activeMediaPaths = []
        self._usedMediaPaths   = []
        self._mediaSplitBases  = set ()

    def init (self, dirpath, exts):
        if self.size ():
            return -2                   # close the door: already initialized

        for _dpath, _, _fnames in os.walk (dirpath):
            for _fname in _fnames:
                _pushPath = exts is None

                if not _pushPath:
                    _splitBase, _ext = os.path.splitext (_fname)
                    _pushPath = _ext in exts

                if _pushPath:
                    self._mediaSplitBases.add (_splitBase)
                    _path = os.path.join (_dpath, _fname)
                    self._activeMediaPaths.append (_path)

            break       # only examine top-level directory

        return 0 if self.size () else 1

    def size (self):
        return len (self._activeMediaPaths)

    def splitBases (self):
        return self._mediaSplitBases

    def getRandom (self):
        numActive = self.size ()

        if numActive:
            _idx  = random.randrange (numActive)
            _path = self._activeMediaPaths.pop (_idx)
            
            self._usedMediaPaths.append (_path)

            if not self.size ():
               self._activeMediaPaths, self._usedMediaPaths = self._usedMediaPaths, self._activeMediaPaths

            return _path

        else:

            return None
    

class _VideoPath (_AbsMediaPath):

    def __init__ (self):
        super ().__init__ ()

    def init (self, dirpath):
        return super ().init (dirpath, ('.MP4', '.mp4'))
    

class _ImagePath (_AbsMediaPath):

    def __init__ (self):
        super ().__init__ ()

    def init (self, dirpath):
        return super ().init (dirpath, ('.jpeg', '.jpg', '.JPEG', '.JPG'))


_urlQLock = Condition ()
_urlQueue = []


# Queue URL and notify watchers

def _recvRendezvousMsg (_fromIP, refcon, dataIn):
    _m_json = dataIn.decode (encoding = 'UTF-8')
    _m_dict = json.loads (_m_json)
    
    diagPrint(f"in recvRendezvousMsg {_m_json} {_fromIP}")

    if isinstance (_m_dict, dict):
        with _urlQLock:
            _urlQueue.append ((_m_dict, refcon))
            _urlQLock.notify ()


class Whiteboard (AbsWhiteboard):

    IOManager.SetProcessMsg (_recvRendezvousMsg, IOM_MT_D_SVR)

    STEG_URL_KEY  = 'url'
    STEG_SEED_KEY = 'seed'

    @staticmethod
    def _removePath (_path):
        if os.path.exists (_path):
            if   os.path.isfile (_path):
                os.remove (_path)

            elif os.path.isdir  (_path):
                for _dpath, _dnames, _fnames in os.walk (_path, topdown = False):
                    for _dname in _dnames:
                        os.rmdir  (os.path.join (_dpath, _dname))
                    for _fname in _fnames:
                        os.remove (os.path.join (_dpath, _fname))

    @staticmethod
    def _makeTempPath (suffix = None, prefix = None, dir = None, text = False, callback = None):
        _fd, _path = tempfile.mkstemp (suffix = suffix, prefix = prefix, dir = dir, text = text)
        os.close (_fd)

        if callback:
            Whiteboard._removePath (_path)
            callback (_path)

        return _path

    def __init__ (self, user, credentials, userContext, wbInstance, wbCConfig):


        
        
        # Prevent direct instantiation of this class

        _type = type (self)
        #_type = None           # for debugging, activate this statement

        diagPrint(f"Initiating Dash Server {_type}")

        if _type == __class__:
            raise NotImplementedError ('{} may not be instantiated'.format (_type))

        # Initialization

        super ().__init__ (user, credentials, userContext, wbInstance, wbCConfig)

        assert isinstance (wbInstance, dict), 'bad or missing wbInstance'
        assert isinstance (wbCConfig,  dict), 'bad or missing wbCConfig'

        _image_cover_dir = wbCConfig.get ('image_cover_dir', None)
        assert _image_cover_dir and os.path.isdir (_image_cover_dir), f'bad or missing wbCConfig:"image_cover_dir" ({_image_cover_dir})'

        _image_path = _ImagePath ()
        assert _image_path.init (_image_cover_dir) == 0, f'"image_cover_dir" ({_image_cover_dir}) contains no image files'

        _video_cover_dir = wbCConfig.get ('video_cover_dir', None)
        assert _video_cover_dir and os.path.isdir (_video_cover_dir), f'bad or missing wbCConfig:"video_cover_dir" ({_video_cover_dir})'

        _video_path = _VideoPath ()
        assert _video_path.init (_video_cover_dir) == 0, f'"video_cover_dir" ({_video_cover_dir}) contains no media files'

        #self.video_caps = ((3000000,'camara-hlondres-squashed.mp4'), (500000, 'soggy.mp4'), (1000000, 'jp-shibuya-squashed.mp4'), (4000000, 'yubatake-1.mp4'), (5000000, 'yubatake-5.mp4'), (6400000, 'osaka-dotonbori-1.mp4'), (7600000, 'osaka-dotonbori-4.mp4'), (None, 'crows-squashed-short.mp4'))


        
        self.video_caps = ((130000,'crows_320.mp4'), (500000, 'crows1_320.mp4'))
        
        
        for _, _vid_cover in self.video_caps:
            vid_cover_path = os.path.join(_video_cover_dir, _vid_cover)
            assert os.path.isfile(vid_cover_path), f'{vid_cover_path} not found'

        #_base_delta = _video_path.splitBases () - _image_path.splitBases ()
        #assert len (_base_delta) == 0, f'"image_cover_dir" ({_image_cover_dir}) missing images for video basename(s) {_base_delta}'

        _encode_app = wbCConfig.get ('encode_app', None)
        assert _encode_app and os.path.isfile (_encode_app), f'bad or missing wbCConfig:"encode_app" ({_encode_app})'

        _decode_app = wbCConfig.get ('decode_app', None)
        assert _decode_app and os.path.isfile (_decode_app), f'bad or missing wbCConfig:"decode_app" ({_decode_app})'

        _image_steg_dir = wbCConfig.get ('image_steg_dir', None)
        assert _image_steg_dir and os.path.isdir (_image_steg_dir), f'bad or missing wbCConfig:"image_steg_dir" ({_image_steg_dir})'

        _video_steg_dir = wbCConfig.get ('video_steg_dir', None)
        assert _video_steg_dir and os.path.isdir (_video_steg_dir), f'bad or missing wbCConfig:"video_steg_dir" ({_video_steg_dir})'

        diagPrint(f"Initiating Dash Server: Done with asserts")

        self.image_cover_dir = _image_cover_dir  
        self.image_path      = _image_path
        self.video_cover_dir = _video_cover_dir  
        self.video_path      = _video_path
        self.encode_app      = _encode_app
        self.decode_app      = _decode_app  
        self.image_steg_dir  = _image_steg_dir  
        self.video_steg_dir  = _video_steg_dir  

        self.recvThread      = None
        self.recvQLock       = Condition ()
        self.recvQueue       = []

    # Use credentials, wbInstance, and wbCConfig maps to open and return a channel.
    #
    # user           # 'Bob Evans'
    # credentials    # {'account': 'BobEvans', 'password': '@bob_evans312'}
    # userContext    # {}
    # wbInstance     # {'class': 'DashSvr',
    #                   'image_cover_dir': '/image/comms/covers/jpeg',
    #                   'video_cover_dir': '/image/comms/covers/video',
    #                   'encode_app':      '/image/comms/source/video_steg/to_dash_svr.sh',
    #                   'decode_app':      '/image/comms/source/video_steg/video_unwedge',
    #                   'image_steg_dir':  '/image/comms/steg/jpeg',
    #                   'video_steg_dir':  '/image/comms/steg/dash'}
    # wbCConfig      # {'driver_path': '/usr/local/bin/geckodriver'}

    def openChannel (self, user, credentials, userContext, wbInstance, wbCConfig):
        return True     # subclass must implement and return channel object

    # Close the channel

    def closeChannel (self, channel):
        pass            # subclass must implement

    # Wait for and return inbound message 

    def recvMsg (self, userContext):

        if self.recvThread is None:
            _t_name = f'DashSvr-recvMsg-{self._user}'
            self.recvThread = self.startThread (_t_name, self._decodeDashStream, (userContext, ))

        while True:
            with self.recvQLock:
                if self.recvQueue:
                    return self.recvQueue.pop (0)
                else:
                    self.recvQLock.wait ()



    def unpack_messages (self, blob, blen):
        idx = 0
        msgList = []

        while (idx < blen):
            mlen = int.from_bytes(blob[idx:idx+4], 'big')
            msg = blob[idx+4:idx+4+mlen]
            msgList.append (msg)
            print (f"unpacked msg {idx} = {mlen} ")
            idx = idx + mlen + 4

        return msgList

    # Pop URL and fetch message from Dash stream
    def _decodeDashStream (self, userContext):       # Thread runnable
        while True:
            _stegDict = None

            with _urlQLock:
                if _urlQueue:
                    _stegDict, refcon = _urlQueue.pop (0)
                else:
                    _urlQLock.wait ()

            if _stegDict:

                _stegURL  = _stegDict.get (self.STEG_URL_KEY)
                _stegSeed = _stegDict.get (self.STEG_SEED_KEY)

                # Create message output path

                vu_tmp_path = self._makeTempPath (prefix = 'vu-', suffix = '.vu', dir = '/tmp',
                                                  callback = lambda _x: os.mkdir (_x))

                vu_msg_path = self._makeTempPath (suffix = '.msg', dir = vu_tmp_path)

                # Invoke video_unwedge

                try:
                    diagPrint (f'calling video_unwedge with -message {vu_msg_path}, -steg {_stegURL}')

                    if 'mp4.mpd' in _stegURL:
                        _stegURL = _stegURL.replace('mp4.mpd', 'MP4.mpd')
                        proc_stat = subprocess.run ([self.decode_app, '-steg', _stegURL, '-bpf', '2', '-nfreqs', '12', '-maxfreqs', '12', '-mcudensity', '100', '-seed', '1', '-message', vu_msg_path, '-quality', '30'],
                                                    stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
                    else:
                        proc_stat = subprocess.run ([self.decode_app, '-steg', _stegURL, '-bpf', '1', '-nfreqs', '12', '-maxfreqs', '12', '-mcudensity', '100', '-seed', '1', '-message', vu_msg_path, '-quality', '30'],
                                                stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
                    diagPrint (f'video_unwedge return code: {proc_stat.returncode}')

                    _unwedge_log = self._makeTempPath (prefix = 'uw-', suffix = '.log', dir = '/log' if os.path.isdir ('/log') else '/tmp')
                    with open (_unwedge_log, 'wb') as _log_out:
                        _log_out.write (proc_stat.stdout)

                    retval = proc_stat.returncode == 0
                except Exception as e:
                    diagPrint (f'video_unwedge threw exception {e}')
                    retval = False

                if retval:
                    with open (vu_msg_path, 'rb') as f_in:
                        _blob = f_in.read ()

                    with self.recvQLock:
                        blob_len = len (_blob)
                        
                        if blob_len > 0:
                            msgList = self.unpack_messages (_blob, blob_len)
                            
                            for j in range ( len(msgList) ):
                                self.recvQueue.append ( msgList[j] )
                            self.recvQLock.notify ()

                self._removePath (vu_tmp_path)


    def getMaxSendMsgCount (self):
        return 500

    def getMaxBlobSize (self):
        return 16000000


    def packMessages (self, msgList):
        blob = bytearray()
        
        for j in range(len(msgList)):
            c = len(msgList[j]).to_bytes(4, 'big')
            blob.extend(c) 
            blob.extend(msgList[j])
            
        return blob

            
    # Send a message.  Return True if successful, False if retry.
    def sendMsg (self, destContext, msgList):

#        msg = msgList[0]
        msg_blob = self.packMessages(msgList)
        
        diagPrint(f"Entering DashSrvr sendMsg: {len(msgList)} messages")
        
        # Write the message to a temporary file

        msg_path = self._makeTempPath (suffix = '.bin', dir = '/tmp')

        with open (msg_path, 'wb') as f_out:
            f_out.write (msg_blob)

        # Select a random cover MP4 and create a randomly named symlink in /tmp

        #        video_path = self.video_path.getRandom ()

        len_msg    = len (msg_blob)
        _vid_cover = None
        boost_flag = 0


        #if (len_msg < 130000):
        #    coverlist = ['crows_130.mp4', 'crows1_130.mp4', 'crows2_130.mp4', 'osaka1_130.mp4', 'osaka2_130.mp4', 'osaka3_130.mp4', 'osaka4_130.mp4', 'yubatake1_130.mp4', 'yubatake2_130.mp4', 'yubatake3_130.mp4', 'yubatake4_130.mp4', 'yubatake5_130.mp4', 'plexus_130.mp4', 'mountains_130.mp4', 'jpshibuya_130.mp4']

        if (len_msg < 130000):
            coverlist = ['crows_130.mp4']

        #elif (len_msg < 320000):
        #    coverlist = ['crows_320.mp4', 'crows1_320.mp4', 'crows2_320.mp4', 'osaka1_320.mp4', 'osaka2_320.mp4', 'osaka3_320.mp4', 'osaka4_320.mp4', 'yubatake1_320.mp4', 'yubatake2_320.mp4', 'yubatake3_320.mp4', 'yubatake4_320.mp4', 'yubatake5_320.mp4', 'plexus_320.mp4', 'mountains_320.mp4', 'jpshibuya_320.mp4']

        elif (len_msg < 320000):
            coverlist = ['crows_320.mp4']

        #elif (len_msg < 2050000):
        #    coverlist = ['crows1_320_x2.mp4', 'osaka3_320_x2.mp4']
        #    boost_flag = 1
            
        #elif (len_msg < 3250000):
        #    coverlist =  ['crows1_130_x25.mp4', 'osaka2_130_x25.mp4', 'osaka3_130_x25.mp4', 'osaka4_130_x25.mp4',
        #                  'yubatake2_130_x25.mp4', 'yubatake3_130_x25.mp4', 'yubatake4_130_x25.mp4'
        #                  'yubatake5_130_x25.mp4']

        elif (len_msg < 3250000):
            coverlist =  ['crows1_130_x25.mp4']

        #elif (len_msg < 4100000):
        #    coverlist = ['crows1_320_x4.mp4', 'osaka3_320_x4.mp4']
        #    boost_flag = 1

        elif (len_msg < 4100000):
            coverlist = ['crows1_320_x4.mp4']
            boost_flag = 1


        elif (len_msg <= 8000000):
            coverlist =  ['crows1_320_x25.mp4', 'osaka3_320_x25.mp4', 'osaka4_320_x25.mp4']

        elif (len_msg <= 16000000):
            coverlist =  ['crows1_320_x25.mp4']
            boost_flag = 1
            
        else:
            diagPrint (f"Message size too large .... {len_msg}.  Max supported size is 8 MB")
            return None
            
                          
        _vid_cover = coverlist[random.randrange(len(coverlist))] # random.choice(coverlist)

            

        video_path = os.path.join(self.video_cover_dir, _vid_cover)
        sym_path   = self._makeTempPath (suffix = '.mp4', dir = '/tmp',
                                         callback = lambda _x: os.symlink (video_path, _x))
        dest, _    = destContext
        m_seed     = self.makeKey (dest)

        # Invoke to_dash_svr.sh

        diagPrint (f"Invoking to_dash_svr {self.encode_app} {video_path} {sym_path} {msg_path} {self.video_steg_dir} {boost_flag} 1")

        try:

            if boost_flag == 0:        
                proc_stat = subprocess.run ([self.encode_app, video_path, sym_path, msg_path, self.video_steg_dir, '1'])
            else:
                proc_stat = subprocess.run ([self.encode_app, video_path, sym_path, msg_path, self.video_steg_dir, '1', '1'])

        except Exception as e:
            diagPrint (f'Uncaught exception in subprocess call {e}')
            return None
            
        diagPrint (f"to_dash_svr returned {proc_stat.returncode}")

        retval = proc_stat.returncode == 0

        if retval:

            # Post a rendezvous message containing the Dash manifest URL and seed

            m_base, _ = os.path.splitext (os.path.basename (sym_path))

            diagPrint(f"m_base is {m_base}")

            m_url  = f'https://{self.getWBTransportMember("persona")}/dash/{m_base}_MP4.mpd'   # see to_dash_svr.sh

            
            diagPrint(f"m_url is {m_url}")

            if boost_flag:
                m_url = m_url.replace("MP4.mpd", "mp4.mpd")
                
            m_dict = {self.STEG_SEED_KEY: m_seed, self.STEG_URL_KEY: m_url}
            m_json = json.dumps (m_dict)

            diagPrint(f"Calling IOManager Send: wb_transp.destAccts = {self._wb_transp.wbDestAccts}")
            IOManager.Send (m_json.encode (), dest, IOM_CT_GENERAL, self._wb_transp, IOM_MT_D_SVR)

        # Clean up

        #os.remove (msg_path)
        os.remove (sym_path)

        return retval   # return status
