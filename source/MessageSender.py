import hashlib
from threading import Condition

from AbsWhiteboard import AbsWhiteboard
from IOManager import IOManager, MessageWrapper, IOM_PARTIAL_MSG, IOM_CT_ORDERED, IOM_MT_CT_COPY
from IPSupport import IPSupport
from DiagPrint import diagPrint

class MessageSender (object):
    _messageSenders = {}

    @classmethod
    def messageSender (cls, dest, wbTransport, timeout = None, maxQueuedBytes = 0, whiteboards = None):
        _dHost     = IPSupport.IP_address (dest)
        _msgSender = cls._messageSenders.get (_dHost, None)
        if _msgSender is None:
            _msgSender = cls (dest, wbTransport, timeout, maxQueuedBytes, whiteboards)
            cls._messageSenders[_dHost] = _msgSender

        return _msgSender

    def __init__ (self, dest, wbTransport, timeout, maxQueuedBytes, whiteboards):
        super ().__init__ ()

        self._dest        = dest
        self._timeout     = timeout
        self._maxQBytes   = maxQueuedBytes

        self._msgWrapper  = MessageWrapper ()
        self._queue       = []
        self._queueLock   = Condition ()
        self._queuedBytes = 0
        self._sender, _   = wbTransport.senderFor (IPSupport.dottedIPStr (dest), _whiteboards = whiteboards)
        self._sOutputLock = self._sender.outputLock ()
        self._sendThread  = None

    def _IOManagerSend (self):
        with self._queueLock:
            lQueue = len (self._queue)
            #diagPrint (f'_IOManagerSend lQueue = {lQueue}')
            if lQueue:
                
                # Pack multiple messages
                
                if lQueue > 1:
                    while self._queue:
                        _msg, cType, refcon, mType = self._queue.pop (0)
                        self._msgWrapper.wrap (_msg, mType, self._dest)

                        m = hashlib.new ('md5')
                        m.update (_msg)
                        diagPrint (f"MessageSender: _IOManagerSend multi-message: {m.hexdigest ()} {len (_msg)}")

                    _, data = self._msgWrapper.close ()
                    diagPrint (f"MessageSender: _IOManagerSend after _msgWrapper.close(): {lQueue}")

                # Send singleton message

                else:
                    data, cType, refcon, mType = self._queue.pop (0)
                    diagPrint (f"MessageSender: _IOManagerSend popping singleton cType: {cType}")

                    m = hashlib.new ('md5')
                    m.update (data)
                    diagPrint (f"MessageSender: _IOManagerSend single message: {m.hexdigest ()} {len (data)}")

                self._queuedBytes = 0

                rval = IOManager.Send (data, IPSupport.Persona_IP_string(self._dest), cType, refcon, mType)
            else:
                rval = IOM_PARTIAL_MSG

        #diagPrint (f'_IOManagerSend rval = {rval}')

        return rval

    def sendMessage (self, message, cType, refcon, mType = IOM_MT_CT_COPY):
        with self._queueLock:
            self._queue.append ((message, cType, refcon, mType if mType != IOM_MT_CT_COPY else cType))
            self._queuedBytes += MessageWrapper.WrappedSize (len (message))

        if self._sender.queueCount () == 0 or (self._maxQBytes and self._queuedBytes >= self._maxQBytes):
            return self._IOManagerSend ()

        else:

            # Provisionally start the notification thread

            if self._sendThread is None:
                self._sendThread = AbsWhiteboard.startThread ('{}-{}'.format (self.__class__.__name__,
                                                                              self._dest),
                                                              self._threadRunnable)
            return IOM_PARTIAL_MSG

    def _threadRunnable (self):
        while True:
            with self._sOutputLock:
                self._sOutputLock.wait (self._timeout)

            _ = self._IOManagerSend ()
