#!/usr/bin/env python3

import argparse 
from enum import Enum, auto
import json
import os
import random
import socket
import sys
from threading import Condition
import time

from IOManager import *
from MessageSender import MessageSender


class _SendTests (Enum):
    DIRECT_SEND  = auto ()
    BROADCAST    = auto ()
    PACKED       = auto ()
    RANDOM_IMAGE = auto ()
    GARBAGE      = auto ()

_sortedSendTests = list (map (lambda _e: _e.name, _SendTests))
_sortedSendTests.sort ()

_count     = None

_sendTests = None       # implicitly all tests (see _parseArgs ())
_args      = None

_RACE_DIR  = '' # path to destini-sri/external/so-builder
_IMAGE_DIR = f'{_RACE_DIR}/covers/jpeg'
_CAP_FILE  = 'capacities.txt'
_J_WRAPPER = f'jel2_codec.sh'

_BASE_HOST = '10.10.1.1'
_EXT_HOST1 = '192.168.100.100'
_EXT_HOST2 = '192.168.222.222'

_extHosts  = [_EXT_HOST1, _EXT_HOST2]

_NUM_EXT   = 2

_bcHosts   = ['www.google.com', 'www.mit.edu']

_CODECS    = \
    {
        "JEL2": {
            "media": {
                "capacities": f"{_IMAGE_DIR}/{_CAP_FILE}",
                "maximum": 4000
            },
            "path": _J_WRAPPER,
            "args": {
                "common": "-seed <secret> -nfreqs 1 -maxfreqs 4",
                "encode": "-quality 75 <coverfile>"
            }
        }
    }


# https://gist.github.com/cslarsen/1595135

def _ipString (ip):
    "Convert 32-bit integer to dotted IPv4 address."
    ip = socket.ntohl (ip)
    return ".".join (map (lambda n: str (ip >> n & 0xFF), [24, 16, 8, 0]))


class _FauxWBTSender (object):
    
    _senders = {}
    
    @classmethod
    def senderFor (cls, dest):
        _sender = cls._senders.get (dest, None)
        if _sender is None:
            _sender = _FauxWBTSender ()
            cls._senders[dest] = _sender
        
        return _sender, None
    
    @classmethod
    def flush (cls):
        for _sender in cls._senders.values ():
            _sender.notify ()

    def __init__ (self):
        self._outLock = Condition ()

    def outputLock (self):
        return self._outLock
    
    def queueCount (self):
        return 1

    def notify (self):
        with self._outLock:
            self._outLock.notify ()


class _DataSegment (object):

    _dataSegments = []

    def __init__ (self, dstIP, refcon, pMsg):
        super ().__init__ ()

        self._dstIP  = dstIP
        self._refcon = refcon
        self._pMsg   = pMsg

    @classmethod
    def SaveSegment (cls, dstIP, refcon, pMsg):
        print ('SaveSegment ({}, {}, {})'.format (_ipString (dstIP), len (pMsg), refcon))

        cls._dataSegments.append (_DataSegment (dstIP, refcon, pMsg))

    @classmethod
    def Examine (cls):
        for _dataSegment in cls._dataSegments:
            _dataSegment.examine ()

    @classmethod
    def CleanUp (cls):
        del cls._dataSegments

    def examine (self):
        print ('IOManager.Examine ({}, {}): {}'.format (len (self._pMsg), _ipString (self._dstIP), IOManager.Examine (self._pMsg, 0, self, ['JEL2'])))


def _processMsg (_fromIP, refcon, pMsg, mTypeStr = ''):

    _lMsg = len (pMsg)
    if _lMsg > 64:             # Assume "large" messages are binary data
        _pMsg = 'len (pMsg): {}'.format (_lMsg)
    else:
        _pMsg = pMsg

    print ('_processMsg ({}): {} ({})'.format (mTypeStr, _pMsg, refcon))

def _processGenericMsg (_fromIP, refcon, pMsg):

    _processMsg (_fromIP, refcon, pMsg)

def _processDSvrMsg (_fromIP, refcon, pMsg):

    _processMsg (_fromIP, refcon, pMsg, 'DSvr')

def _sendMsg (dstIP, refcon, pMsg, cType = IOM_MT_GENERAL):

    print (f'_sendMsg (, {refcon}, {len (pMsg)}, {cType})')
    _DataSegment.SaveSegment (dstIP, refcon, pMsg)

    return 0

def _setHostIP (hostname = None):

    if hostname:
        print ('IOManager.SetHostIP ({}): {}'.format (hostname, IOManager.SetHostIP (hostname)))
    else:
        print ('IOManager.SetHostIP (): {}'.format (IOManager.SetHostIP ()))

def _isValidTest (_parser, arg):

    try:
        return _SendTests[arg]
    except:
        _parser.error ('"{}" is not a valid _SendTests enum: must be one of {}.'
                       .format (arg, _sortedSendTests))

def _parseArgs ():

    print ('# {}'.format (' '.join (sys.argv)))

    _parser = argparse.ArgumentParser ()
    _parser.add_argument ('-t', '--test',
                          action  = 'append',
                          type    = lambda x: _isValidTest (_parser, x),
                          help    = 'one of {}; may be repeated'.format (_sortedSendTests))
    _parser.add_argument ('-c', '--count',
                          default = 1,
                          type    = int,
                          help    = 'number of times to run (default: %(default)s)')
    _parser.add_argument ('msg',
                          type    = str,
                          nargs   = '+',
                          help    = 'Message string, "-r", "--random", or path')

    _cli_args  = _parser.parse_args ()
    _tests     = _cli_args.test

    global _sendTests, _count, _ECC_METHOD, _args

    _sendTests  = set (_tests if _tests else _SendTests)
    _count      = _cli_args.count
    _args       = _cli_args.msg

_doStaticInitialize = True
_baseCodec          = None

def _initialize ():

    global _doStaticInitialize

    if _doStaticInitialize:

        _doStaticInitialize = False

#        SetDiagPrint (print)

        print (f'codecsSpec: {json.dumps (_CODECS)}', flush = True)

        print ('CLICodec.SetCodecsSpec (): {}'   .format (_IMAGE_DIR,
                                                          CLICodec.SetCodecsSpec (json.dumps (_CODECS))))
        print ('IOManager.SetProcessMsg ({}): {}'.format (_processGenericMsg,
                                                          IOManager.SetProcessMsg (_processGenericMsg)))
        print ('IOManager.SetProcessMsg ({}): {}'.format (_processDSvrMsg,
                                                          IOManager.SetProcessMsg (_processDSvrMsg,
                                                                                   IOM_MT_D_SVR)))
        print ('IOManager.SetSendMsg ({}): {}'   .format (_sendMsg,
                                                          IOManager.SetSendMsg (_sendMsg)))
        print ('IOManager.SetSendMsg ({}): {}'   .format (_sendMsg,
                                                          IOManager.SetSendMsg (_sendMsg, IOM_MT_D_SVR)))

        for hostname in _bcHosts:
            print (f'IOManager.SetBroadcastHost ("{hostname}")', flush = True)
            IOManager.SetBroadcastHost (hostname)

        for i in range (_NUM_EXT):
            _eHost = _extHosts[i]

            print (f'IOManager.GetToCodec ({_eHost}, "JEL2")', flush = True)
            _codec = IOManager.GetToCodec (_eHost, IOM_CT_GENERAL)

            global _baseCodec

            if _baseCodec is None:
                _baseCodec = _codec

    # (Re)set initial host

    print (f'_setHostIP ({_BASE_HOST})', flush = True)
    _setHostIP (_BASE_HOST)

wbTransport = _FauxWBTSender

_randomArg = ('-r', '--random')

def _sendMsgs (args):

    print (f'_sendMsgs ({args})', flush = True)

    for i in range (_NUM_EXT):
        _eHost = _extHosts[i]

        print ('Sending messages to {}'.format (_eHost))
        
        _msgSender = MessageSender.messageSender (_eHost, wbTransport)

        nArgs = len (args)

        for _arg in args:
            mType  = IOM_MT_D_SVR if nArgs & 1 else IOM_MT_GENERAL;
            refcon = (_eHost, mType)

            if _arg in _randomArg:
                if _SendTests.DIRECT_SEND in _sendTests:
                    _pMedia = _baseCodec.getRandomMedia ()
                    with open (_pMedia.path (), 'rb') as _f:
                        _pImage = _f.read ()

                    count = IOManager.Send (_pImage, _eHost, refcon, mType, IOM_CT_ORDERED, _pMedia)
                    print (f'IOManager.Send ({len (_pImage)}, {_eHost}, {mType}, ..., "{_pMedia.path ()}"): {count}')

            elif os.path.isfile (_arg):
                if _SendTests.DIRECT_SEND in _sendTests:
                    with open (_arg, 'rb') as _f:
                        _pContent = _f.read ()

                    count = IOManager.Send (_pContent, _eHost, refcon, mType)
                    print (f'IOManager.Send ({arg}): {len (_pContent)}, {_eHost}, ..., {mType}): {count}')

            else:
                if _SendTests.DIRECT_SEND in _sendTests:
                    count  = IOManager.Send (_arg.encode (), _eHost, refcon, mType)
                    print ('IOManager.Send ("{}", {}, ..., {}): {}'.format (_arg, _eHost, mType, count))

                if _SendTests.PACKED in _sendTests:
                    _wrappedArg = 'PACKED ({}): {}'.format (_eHost, _arg)

                    status = _msgSender.sendMessage (_wrappedArg.encode (), mType, refcon)
                    print ('MessageSender.sendMessage ({}): {}'.format (_wrappedArg, status))
            
            nArgs -= 1

        # Send a broadcast message

        if _SendTests.BROADCAST in _sendTests:
            for _arg in args:
                _idx      = random.randrange (len (_bc_hosts))
                _bcastArg = f'BROADCAST ({_arg}): {_eHost}'

                retval = IOManager.Broadcast (_bcastArg.encode (), _bc_hosts[_idx], (_eHost, mType), IOM_MT_GENERAL)
                print (f'IOManager.Broadcast ("{_bcastArg}", ..., {mType}): {retval}')
                break

        # Add random (plain) and truncated images

        if _SendTests.RANDOM_IMAGE in _sendTests:
            _pMedia = _baseCodec.getRandomMedia ()
            with open (_pMedia.path (), 'rb') as _f:
                pImage = _f.read ()
            _sendMsg (0, "<plain>", pImage);
            _sendMsg (0, "<truncated>", pImage[:100]);

            _arg  = "DSvr side channel"
            count = IOManager.Send (_arg.encode (), _eHost, (_eHost, mType), mType, IOM_MT_D_SVR, _pMedia)
            print (f'IOManager.Send ("{_arg}", {_eHost}, ..., {mType}, {IOM_MT_D_SVR}, {_pMedia}): {count}', flush = True)

        # Add garbage

        if _SendTests.GARBAGE in _sendTests:
            _sendMsg (0, "<garbage>", b'This is clearly not a JPEG image')
        
    wbTransport.flush ()

def _recvMsgs ():

    time.sleep (1)      # needed for asynchronous wbTransport.flush () side-effects

    for i in range (_NUM_EXT):
        _eHost = _extHosts[i]
        _setHostIP (_eHost)

        IOManager.GetFromCodec (_BASE_HOST, "JEL2")

        _DataSegment.Examine ()

def _cleanup ():

    _setHostIP ()
    _DataSegment.CleanUp ()
    IOManager.CleanUp ()

def main ():

    _parseArgs ()

    for _ in range (_count):
        _initialize ()
        _sendMsgs (_args)
        _recvMsgs ()
        _cleanup ()


if __name__ == '__main__':
    main ()
