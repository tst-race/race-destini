import sys
import time
from threading import Condition

from AbsWhiteboard import Appraisal
from Whiteboard import Whiteboard
from DiagPrint import diagPrint

class Puller (Whiteboard):
    def __init__ (self, user, credentials, userContext, wbInstance, wbCConfig):
        super ().__init__ (user, credentials, userContext, wbInstance, wbCConfig)

        self._userContext = userContext
        self._recvQueue   = []
        self._recvLock    = Condition ()
        self._processMsg  = None
        self._pubThread   = None

    def setProcessMsg (self, processMsg):
        self._processMsg = processMsg

    def start (self, name = None, forceOpenChannel = True):
        super ().start (name, (forceOpenChannel, ))

        # Create and run publication thread

        _threadName = '{}-publish-{}'.format (self._className (), self._user)

        self._pubThread = self.startThread (_threadName, self._publication_run)

    def is_alive (self):
        return self._is_alive (self._pubThread) and super ().is_alive ()

    def _publication_run (self):
        while self._processMsg:

            # Wait for inbound messages

            with self._recvLock:
                while self._recvQueue:
                    msg = self._recvQueue.pop (0)
                  
                    # Invoke application callback
                    diagPrint(f"WBPushPullers: Popping and Processing Message {self._codecs} {self._processMsg}")
                    try:
                        self._processMsg (msg, self._codecs)
                    except Exception as e:
                        diagPrint (f"ERROR: _processMsg exception caught in publication run {e}")
                        
                self._recvLock.wait ()

        diagPrint(f"ERROR: exiting from publication run {self._processMsg}")

    def threadLoop (self):
        while self._channel:    # accommodate the channel being asynchronously closed

            # Wait for inbound messages

            try:
                msg = self.recvMsg (self._userContext)
            except Exception as e:
                diagPrint (f"ERROR: recvMsg failed in threadLoop {e}")
                continue

            if msg is None:     # channel was closed
                break

            diagPrint("WBPushPullers: Message received")

            with self._recvLock:
                self._recvQueue.append (msg)
                self._recvLock.notify ()

        diagPrint("WARNING: Exiting thread loop")

class Pusher (Whiteboard):

    _SEND_Q_STATUS_COUNT = 'send queue count'

    def __init__ (self, user, credentials, userContext, wbInstance, wbCConfig):
        super ().__init__ (user, credentials, userContext, wbInstance, wbCConfig)

        self._sendAppr  = Appraisal.UNTRIED
        self._saConf    = 0
        self._sendQueue = []
        self._sendLock  = Condition ()
        self._tLastSent = 0

    def outputLock (self):
        return self._sendLock;

    #def getMaxSendMsgCount(self):
    #    return 1

    #def getMaxBlobSize(self):
    #    return 20000000

    def queueCount (self):
        return self.getStatus (self._SEND_Q_STATUS_COUNT, 0)

    def pushMsg (self, msg, dest, userContext):
        diagPrint (f"WBPushPullers:  In pushMsg {self.is_alive()}")
        if self.is_alive ():
            with self._sendLock:
                diagPrint(f"WBPusher: push message len {len(msg)} {self._channel}")
                self._sendQueue.append ((msg, dest, userContext))
                self.incrementStatus (self._SEND_Q_STATUS_COUNT)
                self._sendLock.notify_all ()
            return True
        else:
            return False


    # return a list of up to maxCnt additonal messages with matching
    # dest context
    def fetchAdditionalMessages (self, maxCnt, maxSz, destContext):
        msgs = []
        szSoFar = 0
        dest, userContext = destContext
        count = 0
        diagPrint(f"sendQueue len = {len(self._sendQueue)}")
        elem_list = []
        
        for elem in self._sendQueue:
            diagPrint (f"dest = {dest}, {elem[1]}, context = {userContext}, {elem[2]}")
            if elem[1] == dest and elem[2] == userContext:

                elem_len = len (elem[0])
                if szSoFar + elem_len + 4 > maxSz:
                    break
                
                msgs.append(elem[0])
                elem_list.append(elem)
                count = count + 1        
                szSoFar = szSoFar + elem_len + 4
        
                if count == maxCnt:
                    diagPrint (f"breaking... count = {count} {maxCnt}")
                    break
                
        for elem in elem_list:        
            self._sendQueue.remove(elem)
            self.incrementStatus (self._SEND_Q_STATUS_COUNT, -1)
                
        diagPrint(f"sendQueue len = {len(self._sendQueue)}")
        return msgs
    
                    

    def notify (self):
        if self.is_alive ():
            with self._sendLock:
                self._sendLock.notify_all ()
            

    def threadLoop (self):
        diagPrint("WBPushPullers: Entering threadLoop")
        while self._channel:            # accommodate the channel being closed
            while self._channel:        # (ditto)
                with self._sendLock:
                    if self._sendQueue:

                        diagPrint (f"WBPushPUllers: threadLoop: before sendQueue pop {self.getStatus(self._SEND_Q_STATUS_COUNT)}")

                        msg, dest, userContext = self._sendQueue.pop (0)


                        # Notify upstream message providers that the queue is empty

                        if self.incrementStatus (self._SEND_Q_STATUS_COUNT, -1) == 0:
                            self.notify ()

                        maxCnt = self.getMaxSendMsgCount() 
                        msgList = []

                        if maxCnt > 1:
                            maxSize = self.getMaxBlobSize()
                            msgList = self.fetchAdditionalMessages(maxCnt-1, maxSize - len (msg) - 4,
                                                                   (dest, userContext))
                        
                        msgList.insert(0, msg)
                        diagPrint("WBPushPullers: inserting into msgList...")
                        break

                    else:
                        self._sendLock.wait ()
                        diagPrint ("WBPushPUllers: threadLoop: Notified after wait")


            if self._channel is None:   # channel was closed
                diagPrint("ERROR: WBPushPullers: Channel was unexpectedly closed")
                break

            # Send with retry and wait interval

            try_wait = self._try_wait
            ts_start = self.current_posix_time ()
            was_sent = False

            diagPrint(f"WBPushPullers: in thread loop {len (msgList)}")

            for _i in range (self._max_try):
                if self._channel is None:       # accommodate the channel being asynchronously closed
                    break

                try:
                    
                    if self.sendMsg ((dest, userContext), msgList):
                        self._tLastSent = self.current_posix_time ()
                        was_sent        = True
                        break

                except Exception as e:
                    diagPrint(f"Caught unhandled exception in WBPusher {e}")

                time.sleep (try_wait)
                try_wait = eval (self._next_wait) (try_wait)
                
                if try_wait > 30:
                    try_wait = 30
                    
            status_prefix = 'send success' if was_sent else 'send failure'
            t_total       = self.current_posix_time () - ts_start

            self.incrementStatus ('{} count'   .format (status_prefix))
            self.incrementStatus ('{} sum t'   .format (status_prefix), t_total)
            self.incrementStatus ('{} sum t sq'.format (status_prefix), t_total * t_total)

            self._sendAppr, self._saConf = self.appraise ('send', was_sent)
            diagPrint (f"WBPusher: continuing loop {self._status}")

            
        diagPrint ("WBPushPullers: Exiting thread loop")
            # TODO: what happens if sendMsg () never succeeds?

    def getSendAppraisal (self):
        return self._sendAppr, self._saConf


class PushPuller (Puller, Pusher):
    def __init__ (self, user, credentials, userContext, wbInstance, wbCConfig):
        Puller.__init__ (self, user, credentials, userContext, wbInstance, wbCConfig)
        Pusher.__init__ (self, user, credentials, userContext, wbInstance, wbCConfig)

    def start (self):
        Puller.start (self)
        Pusher.start (self, None, (False, ))

    def is_alive (self):
        return Puller.is_alive (self) and Pusher.is_alive (self)
