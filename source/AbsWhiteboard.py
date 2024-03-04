from enum import Enum, auto
import inspect
import socket
import struct
from threading import Thread, RLock
import time
import math

from CLICodec import CLICodec
from DiagPrint import diagPrint
from IPSupport import IPSupport
from UserModel import UserModel


class AutoName (Enum):
    def _generate_next_value_ (name, start, count, last_values):
        return name


class Appraisal (AutoName):
    UNTRIED       = auto ()
    FUNCTIONAL    = auto ()
    MARGINAL      = auto ()
    NONFUNCTIONAL = auto ()


'''
- Initialization
  - Parse link_profile_config.
  - Parse whiteboard.json and reconcile against link_profile_config.
  - Create singleton inbound and multiple site-specific outbound
    message queues and RLock mutuxes

- start ()
  - Create and run puller, pusher, and pushPuller whiteboard threads
    - Connect with exponential backoff and sunset count.  (What do we
      do on connection failure?)
    - Log in
    - Pullers
      - Periodically poll assigned whiteboard site
      - Post to inbound message queue
      - Periodically refresh the connection
    - Pushers
      - Wait on site-specific outbound message queue mutex
      - Periodically refresh the connection
  - Create and run singleton inbound message queue processor

- shutdown ()
  - Terminate all transport threads
  - Empty queues

- sendPackageDirectLink ()
  - If link transport is through a whiteboard, determine the
    corresponding output queue, push the data, and return.
'''

# https://stackoverflow.com/questions/8777753/converting-datetime-date-to-utc-timestamp-in-python

from datetime import datetime, timezone, timedelta

_dt_utc  = datetime (1970, 1, 1, tzinfo = timezone.utc)
_t_del_1 = timedelta (seconds = 1)


class AbsWhiteboard (object):

    #############
    # Constants #
    #############

    _MAX_APPRAISALS = 6         # maximum number of appraisal success values in _appraisal value lists

    ###################
    # Class variables # *** TODO: THIS IS BROKEN FOR MULTIPLE CONCURRENT WHITEBOARDS! ***
    ###################

    WB_STATUS             = False
    WB_STATUS_CHANGE_TIME = 0


    ###################
    # Utility methods #
    ###################

    # Check if thread is alive

    @staticmethod
    def _is_alive (_thread):
        return _thread and _thread.is_alive ()

    # Create and start a thread

    @staticmethod
    def startThread (tName, tTarget, tArgs = (), daemon = True):
        _thread = Thread (target = tTarget,
                          name   = tName,
                          args   = tArgs,
                          daemon = daemon)
        _thread.start ()

        return _thread

    # Return network-ordered IP address from host string

    @staticmethod
    def ipv4FromHost (hostname):
        return IPSupport.IP_address (hostname)

    # Return current time in POSIX seconds

    @staticmethod
    def current_posix_time ():
        _dt = datetime.now (timezone.utc)

        return (_dt - _dt_utc) / _t_del_1

    # Return class name

    def _className (self):
        return self.__class__.__name__

    ####################
    # Instance methods #
    ####################

    def __init__ (self, user, credentials, uContext, wbInstance, wbCConfig):

        # Prevent direct instantiation of this class

        _type = type (self)

        if _type == __class__:
            raise NotImplementedError ('{} may not be instantiated'.format (_type))

        # Initialization

        super ().__init__ ()

        self._appraisal = {}    # key: <function>, value: success array

        self._wb_transp = None
        self._wb_tr_get = None

        self._channel   = None
        self._codecs    = None
        self._conn_appr = Appraisal.UNTRIED
        self._ca_confid = 0
        self._wbThread  = None
        self._user      = user
        self._cred      = credentials
        self._ucontext  = uContext
        self._inst      = wbInstance
        self._cconfig   = wbCConfig
        self._userModel = None

        self._defineRetryParams ()

        self._status   = {}
        self._st_lock  = RLock ()

    def _setWBTransport (self, wbTransp, wbTransGet):
        self._wb_transp = wbTransp
        self._wb_tr_get = wbTransGet

        if self._userModel is None:
            _userModel = self._inst.get ('userModel')
            if _userModel:
                self._userModel = UserModel (_userModel)

    def getWBTransportMember (self, key):
        return self._wb_tr_get (key)

    @property
    def userModel (self):
        return self._userModel
    
    # User model method
    def trackAdd (self, nBytes = 0, nItems = 1, _id = None, _type = 'data'):
        if self._userModel:
            self._userModel.trackAdd (nBytes, nItems, _id, _type)

    def makeKey (self, destHost):
        _persona = self.getWBTransportMember ('persona')
        _srcIP   = self.ipv4FromHost (_persona)
        _dstIP   = self.ipv4FromHost (destHost)

        return CLICodec.makeSecret (_srcIP, _dstIP)
    
    def defineCodecs (self, codecs):
        self._codecs = codecs

    def _defineRetryParams (self):
        self._try_wait  = 4
        self._max_try   = 5
        self._next_wait = 'lambda _t: _t # constant wait interval'

        if isinstance (self._cconfig, dict):
            self._try_wait  = int (self._cconfig.get ('initial_retry_wait', self._try_wait))
            self._max_try   = int (self._cconfig.get ('max_retry_count',    self._max_try))
            self._next_wait =      self._cconfig.get ('next_wait_lambda',   self._next_wait)

    def incrementStatus (self, _key, delta = 1):
        with self._st_lock:
            _val = self._status.get (_key, 0) + delta
            self._status[_key] = _val

        return _val

    def getStatus (self, _key, default = None):
        with self._st_lock:
            _val = self._status.get (_key, default)

        return _val

    def setStatus (self, _key, _val):
        with self._st_lock:
            self._status[_key] = _val

        return _val

    def delStatus (self, _key):
        with self._st_lock:
            _val = self._status.pop (_key, None)

        return _val

    # setTimer: collect timing statistics
    #
    # setTimer (_label)
    #   Start a named timer
    #
    # setTimer (_label, False [, _statusLabel])
    #   End a named timer and define/update the _status dict key entries
    #     <thread name>'-'<_label or _statusLabel>' t '('count', 'sum', 'sum sq')

    def setTimer (self, _label, isStart = True, _realLabel = None):
        if isStart:
            self.setStatus (_label, self.current_posix_time ())

        else:
            _t_start = self.getStatus (_label)
            if _t_start:
                _t_del  = self.current_posix_time () - _t_start
                self.delStatus (_label)

                _prefx   = f'{self._wbThread.name}-' if self.is_alive () else ''
                _v_prefx = f'{_prefx}{_realLabel if _realLabel else _label} t '
                self.incrementStatus (f'{_v_prefx}count')
                self.incrementStatus (f'{_v_prefx}sum',    _t_del)
                self.incrementStatus (f'{_v_prefx}sum sq', _t_del * _t_del)
                
                '''
                count = self.getStatus (f'{_v_prefx}count')

                if count > 2:
                    sum_ = self.getStatus (f'{_v_prefx}sum')
                    sum_squared = self.getStatus (f'{_v_prefx}sum sq')
                    variance = (count * sum_squared - sum_ * sum_) / (count * count)
                    diagPrint(f'label = {_label}, count = {count}, avg = {sum_/count},  var = {math.sqrt(variance)}')
                '''

                _min_key = f'{_v_prefx}min'
                _max_key = f'{_v_prefx}max'

                _min = self.getStatus (_min_key)
                if _min is None:
                    self.setStatus (_min_key, _t_del)
                    self.setStatus (_max_key, _t_del)
                else:
                    if _t_del < _min:
                        self.setStatus (_min_key, _t_del)

                    if _t_del > self.getStatus (_max_key):
                        self.setStatus (_max_key, _t_del)

    def appraise (self, _key, _success = None):

        # Fetch appraisal success list

        _appr_list = self._appraisal.get (_key, None)
        if _appr_list is None:
            _appr_list = []
            self._appraisal[_key] = _appr_list

        # Provisionally append the current success value

        if _success is not None:
            if len (_appr_list) == self._MAX_APPRAISALS:
                _appr_list.pop (0)   # discard oldest value

            _appr_list.append (_success)

        # Appraise the function based upon its history

        num_success = 0
        num_failure = 0

        for _state in _appr_list:
            if _state:
                num_success += 1
            else:
                num_failure += 1

        len_appr_list = len (_appr_list)

        if   num_success == len_appr_list:
            return Appraisal.FUNCTIONAL,    int (100 * num_success / self._MAX_APPRAISALS)
        elif num_failure == len_appr_list:
            return Appraisal.NONFUNCTIONAL, int (100 * num_failure / self._MAX_APPRAISALS)
        else:
            _min = min (num_success, num_failure)
            _max = max (num_success, num_failure)
            return Appraisal.MARGINAL,      int (100 * (_min / _max) * (num_success + num_failure) / self._MAX_APPRAISALS)

    def getConnAppraisal (self):
        return self._conn_appr, self._ca_config

    def start (self, name = None, args = ()):
        if self.is_alive ():
            return

        if name is None:
            name = '{}-{}'.format (self._className (), self._user)

        diagPrint(f"AbsWhiteboard start: {name} {args}")
        self._wbThread = self.startThread (name, self._threadRunnable, args)

    def is_alive (self):
        return self._is_alive (self._wbThread)

    # threadLoop: virtual implementation

    def threadLoop (self):
        # https://stackoverflow.com/questions/33162319/how-can-get-current-function-name-inside-that-function-in-python
        raise NotImplementedError ('{}.{} () not implemented'.format (self._className (),
                                                                      inspect.getframeinfo (inspect.currentframe ()).function))

    def _threadRunnable (self, forceOpenChannel = False):
        if self._channel is None or forceOpenChannel:
            try:
                self._closeChannel ()           
                self._openChannel ()
            except Exception as e:
                diagPrint (f"ERROR: Caught thread exception in AbsWhiteboard _threadRunnable {e}")
                return
                
            if self._channel is None:
                diagPrint(f"ERROR: AbsWhiteboard: threadRunnable: no channel")
                return

        try:
            self.threadLoop ()
        except Exception as e:
            diagPrint (f"ERROR: threadLoop caught exception in AbsWhiteboard {e}")

    def _openChannel (self):
        try_wait = self._try_wait
        channel  = None
        self.setTimer ('_openChannel')
        diagPrint ('IN ABS_OPEN_CHANNEL')

        # Run connection loop

        for _i in range (self._max_try):
            try:
                channel = self.openChannel (self._user, self._cred, self._ucontext, self._inst, self._cconfig)
                if channel:
                    self._channel = channel
                    break
            except:
                pass

            time.sleep (try_wait)
            try_wait = eval (self._next_wait) (try_wait)

        self.setTimer ('_openChannel', False, 'open success' if channel else 'open failure')

        self._conn_appr, self._ca_config = self.appraise ('open', channel is not None)

        return channel

    def _closeChannel (self):
        if self._channel:
            try:
                self.closeChannel (self._channel)   # TODO: implement retry loop?
            except:
                pass
            self._channel = None

    ###################
    #                 #
    # Virtual methods #
    #                 #
    ###################

    # Use credentials, user context, instance, and class to open a channel

    def openChannel (self, user, credentials, userContext, wbInstance, wbCConfig):
        # https://stackoverflow.com/questions/33162319/how-can-get-current-function-name-inside-that-function-in-python
        raise NotImplementedError ('{}.{} () not implemented'.format (self._className (),
                                                                      inspect.getframeinfo (inspect.currentframe ()).function))

    # Close the channel

    def closeChannel (self, channel):
        # https://stackoverflow.com/questions/33162319/how-can-get-current-function-name-inside-that-function-in-python
        raise NotImplementedError ('{}.{} () not implemented'.format (self._className (),
                                                                      inspect.getframeinfo (inspect.currentframe ()).function))

    # Wait for and return inbound message 

    def recvMsg (self, userContext):
        # https://stackoverflow.com/questions/33162319/how-can-get-current-function-name-inside-that-function-in-python
        raise NotImplementedError ('{}.{} () not implemented'.format (self._className (),
                                                                      inspect.getframeinfo (inspect.currentframe ()).function))

    def sendMsg (self, destContext, msg):
        # https://stackoverflow.com/questions/33162319/how-can-get-current-function-name-inside-that-function-in-python
        raise NotImplementedError ('{}.{} () not implemented'.format (self._className (),
                                                                      inspect.getframeinfo (inspect.currentframe ()).function))
