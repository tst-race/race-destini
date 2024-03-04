# This file was automatically generated by SWIG (http://www.swig.org).
# Version 3.0.12
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

import os
import sys
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, f"{CURRENT_PATH}/libs")

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import IOManager
else:
    import IOManager

from sys import version_info as _swig_python_version_info
if _swig_python_version_info >= (2, 7, 0):
    def swig_import_helper():
        import importlib
        pkg = __name__.rpartition('.')[0]
        mname = '.'.join((pkg, '_IOManager')).lstrip('.')
        try:
            return importlib.import_module(mname)
        except ImportError:
            return importlib.import_module('_IOManager')
    _IOManager = swig_import_helper()
    del swig_import_helper
elif _swig_python_version_info >= (2, 6, 0):
    def swig_import_helper():
        from os.path import dirname
        import imp
        fp = None
        try:
            fp, pathname, description = imp.find_module('_IOManager', [dirname(__file__)])
        except ImportError:
            import _IOManager
            return _IOManager
        try:
            _mod = imp.load_module('_IOManager', fp, pathname, description)
        finally:
            if fp is not None:
                fp.close()
        return _mod
    _IOManager = swig_import_helper()
    del swig_import_helper
else:
    import _IOManager
del _swig_python_version_info

try:
    _swig_property = property
except NameError:
    pass  # Python < 2.2 doesn't have 'property'.

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_setattr_nondynamic(self, class_type, name, value, static=1):
    if (name == "thisown"):
        return self.this.own(value)
    if (name == "this"):
        if type(value).__name__ == 'SwigPyObject':
            self.__dict__[name] = value
            return
    method = class_type.__swig_setmethods__.get(name, None)
    if method:
        return method(self, value)
    if (not static):
        if _newclass:
            object.__setattr__(self, name, value)
        else:
            self.__dict__[name] = value
    else:
        raise AttributeError("You cannot add attributes to %s" % self)


def _swig_setattr(self, class_type, name, value):
    return _swig_setattr_nondynamic(self, class_type, name, value, 0)


def _swig_getattr(self, class_type, name):
    if (name == "thisown"):
        return self.this.own()
    method = class_type.__swig_getmethods__.get(name, None)
    if method:
        return method(self)
    raise AttributeError("'%s' object has no attribute '%s'" % (class_type.__name__, name))


def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)

try:
    _object = object
    _newclass = 1
except __builtin__.Exception:
    class _object:
        pass
    _newclass = 0

class SwigPyIterator(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, SwigPyIterator, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, SwigPyIterator, name)

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined - class is abstract")
    __repr__ = _swig_repr
    __swig_destroy__ = _IOManager.delete_SwigPyIterator
    __del__ = lambda self: None

    def value(self):
        return _IOManager.SwigPyIterator_value(self)

    def incr(self, n=1):
        return _IOManager.SwigPyIterator_incr(self, n)

    def decr(self, n=1):
        return _IOManager.SwigPyIterator_decr(self, n)

    def distance(self, x):
        return _IOManager.SwigPyIterator_distance(self, x)

    def equal(self, x):
        return _IOManager.SwigPyIterator_equal(self, x)

    def copy(self):
        return _IOManager.SwigPyIterator_copy(self)

    def next(self):
        return _IOManager.SwigPyIterator_next(self)

    def __next__(self):
        return _IOManager.SwigPyIterator___next__(self)

    def previous(self):
        return _IOManager.SwigPyIterator_previous(self)

    def advance(self, n):
        return _IOManager.SwigPyIterator_advance(self, n)

    def __eq__(self, x):
        return _IOManager.SwigPyIterator___eq__(self, x)

    def __ne__(self, x):
        return _IOManager.SwigPyIterator___ne__(self, x)

    def __iadd__(self, n):
        return _IOManager.SwigPyIterator___iadd__(self, n)

    def __isub__(self, n):
        return _IOManager.SwigPyIterator___isub__(self, n)

    def __add__(self, n):
        return _IOManager.SwigPyIterator___add__(self, n)

    def __sub__(self, *args):
        return _IOManager.SwigPyIterator___sub__(self, *args)
    def __iter__(self):
        return self
SwigPyIterator_swigregister = _IOManager.SwigPyIterator_swigregister
SwigPyIterator_swigregister(SwigPyIterator)

IOM_WHOLE_MSG = _IOManager.IOM_WHOLE_MSG
IOM_PARTIAL_MSG = _IOManager.IOM_PARTIAL_MSG
IOM_OUT_OF_MEM = _IOManager.IOM_OUT_OF_MEM
IOM_NOT_SEGMENT = _IOManager.IOM_NOT_SEGMENT
IOM_DUP_SEGMENT = _IOManager.IOM_DUP_SEGMENT
IOM_BAD_SEG_IDX = _IOManager.IOM_BAD_SEG_IDX
IOM_BAD_NUM_SEG = _IOManager.IOM_BAD_NUM_SEG
IOM_EXPIRED_SEG = _IOManager.IOM_EXPIRED_SEG
IOM_NO_SENDER = _IOManager.IOM_NO_SENDER
IOM_NO_CODEC = _IOManager.IOM_NO_CODEC
IOM_PRFX_MAGIC = _IOManager.IOM_PRFX_MAGIC
IOM_PRFX_IS_SRC = _IOManager.IOM_PRFX_IS_SRC
IOM_PRFX_BRDCST = _IOManager.IOM_PRFX_BRDCST
IOM_PRFX_X_DST = _IOManager.IOM_PRFX_X_DST
IOM_PREF_X_CHK = _IOManager.IOM_PREF_X_CHK
IOM_PREF_X_LEN = _IOManager.IOM_PREF_X_LEN
IOM_CT_ORDERED = _IOManager.IOM_CT_ORDERED
IOM_CT_GENERAL = _IOManager.IOM_CT_GENERAL
IOM_CT_AVIDEO = _IOManager.IOM_CT_AVIDEO
IOM_CT_D_SVR = _IOManager.IOM_CT_D_SVR
IOM_MT_CT_COPY = _IOManager.IOM_MT_CT_COPY
IOM_MT_GENERAL = _IOManager.IOM_MT_GENERAL
IOM_MT_AVIDEO = _IOManager.IOM_MT_AVIDEO
IOM_MT_D_SVR = _IOManager.IOM_MT_D_SVR
class MessageWrapper(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, MessageWrapper, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, MessageWrapper, name)
    __repr__ = _swig_repr

    def __init__(self):
        this = _IOManager.new_MessageWrapper()
        try:
            self.this.append(this)
        except __builtin__.Exception:
            self.this = this
    __swig_destroy__ = _IOManager.delete_MessageWrapper
    __del__ = lambda self: None
    if _newclass:
        WrappedSize = staticmethod(_IOManager.MessageWrapper_WrappedSize)
    else:
        WrappedSize = _IOManager.MessageWrapper_WrappedSize

    def wrap(self, *args):
        return _IOManager.MessageWrapper_wrap(self, *args)

    def close(self, pData=None, nData=None):
        return _IOManager.MessageWrapper_close(self, pData, nData)
MessageWrapper_swigregister = _IOManager.MessageWrapper_swigregister
MessageWrapper_swigregister(MessageWrapper)

def MessageWrapper_WrappedSize(nData):
    return _IOManager.MessageWrapper_WrappedSize(nData)
MessageWrapper_WrappedSize = _IOManager.MessageWrapper_WrappedSize

class IOManager(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, IOManager, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, IOManager, name)
    __repr__ = _swig_repr
    if _newclass:
        AddChannel = staticmethod(_IOManager.IOManager_AddChannel)
    else:
        AddChannel = _IOManager.IOManager_AddChannel
    if _newclass:
        MakeCodecs = staticmethod(_IOManager.IOManager_MakeCodecs)
    else:
        MakeCodecs = _IOManager.IOManager_MakeCodecs
    if _newclass:
        GetFromCodec = staticmethod(_IOManager.IOManager_GetFromCodec)
    else:
        GetFromCodec = _IOManager.IOManager_GetFromCodec
    if _newclass:
        GetToCodec = staticmethod(_IOManager.IOManager_GetToCodec)
    else:
        GetToCodec = _IOManager.IOManager_GetToCodec
    if _newclass:
        SetHostIP = staticmethod(_IOManager.IOManager_SetHostIP)
    else:
        SetHostIP = _IOManager.IOManager_SetHostIP
    if _newclass:
        SetProcessMsg = staticmethod(_IOManager.IOManager_SetProcessMsg)
    else:
        SetProcessMsg = _IOManager.IOManager_SetProcessMsg
    if _newclass:
        SetSendMsg = staticmethod(_IOManager.IOManager_SetSendMsg)
    else:
        SetSendMsg = _IOManager.IOManager_SetSendMsg
    if _newclass:
        SetBroadcastHost = staticmethod(_IOManager.IOManager_SetBroadcastHost)
    else:
        SetBroadcastHost = _IOManager.IOManager_SetBroadcastHost
    if _newclass:
        SetBroadcastIP = staticmethod(_IOManager.IOManager_SetBroadcastIP)
    else:
        SetBroadcastIP = _IOManager.IOManager_SetBroadcastIP
    if _newclass:
        GetBroadcastIPs = staticmethod(_IOManager.IOManager_GetBroadcastIPs)
    else:
        GetBroadcastIPs = _IOManager.IOManager_GetBroadcastIPs
    if _newclass:
        Examine = staticmethod(_IOManager.IOManager_Examine)
    else:
        Examine = _IOManager.IOManager_Examine
    if _newclass:
        Send = staticmethod(_IOManager.IOManager_Send)
    else:
        Send = _IOManager.IOManager_Send
    if _newclass:
        Broadcast = staticmethod(_IOManager.IOManager_Broadcast)
    else:
        Broadcast = _IOManager.IOManager_Broadcast
    if _newclass:
        SetDuration = staticmethod(_IOManager.IOManager_SetDuration)
    else:
        SetDuration = _IOManager.IOManager_SetDuration
    if _newclass:
        CleanUp = staticmethod(_IOManager.IOManager_CleanUp)
    else:
        CleanUp = _IOManager.IOManager_CleanUp

    def __init__(self):
        this = _IOManager.new_IOManager()
        try:
            self.this.append(this)
        except __builtin__.Exception:
            self.this = this
    __swig_destroy__ = _IOManager.delete_IOManager
    __del__ = lambda self: None
IOManager_swigregister = _IOManager.IOManager_swigregister
IOManager_swigregister(IOManager)

def IOManager_AddChannel(cType):
    return _IOManager.IOManager_AddChannel(cType)
IOManager_AddChannel = _IOManager.IOManager_AddChannel

def IOManager_MakeCodecs(*args):
    return _IOManager.IOManager_MakeCodecs(*args)
IOManager_MakeCodecs = _IOManager.IOManager_MakeCodecs

def IOManager_GetFromCodec(*args):
    return _IOManager.IOManager_GetFromCodec(*args)
IOManager_GetFromCodec = _IOManager.IOManager_GetFromCodec

def IOManager_GetToCodec(*args):
    return _IOManager.IOManager_GetToCodec(*args)
IOManager_GetToCodec = _IOManager.IOManager_GetToCodec

def IOManager_SetHostIP(*args):
    return _IOManager.IOManager_SetHostIP(*args)
IOManager_SetHostIP = _IOManager.IOManager_SetHostIP

def IOManager_SetProcessMsg(*args):
    return _IOManager.IOManager_SetProcessMsg(*args)
IOManager_SetProcessMsg = _IOManager.IOManager_SetProcessMsg

def IOManager_SetSendMsg(*args):
    return _IOManager.IOManager_SetSendMsg(*args)
IOManager_SetSendMsg = _IOManager.IOManager_SetSendMsg

def IOManager_SetBroadcastHost(broadcastHost, broadcastSeed=0):
    return _IOManager.IOManager_SetBroadcastHost(broadcastHost, broadcastSeed)
IOManager_SetBroadcastHost = _IOManager.IOManager_SetBroadcastHost

def IOManager_SetBroadcastIP(broadcastIP, broadcastSeed=0):
    return _IOManager.IOManager_SetBroadcastIP(broadcastIP, broadcastSeed)
IOManager_SetBroadcastIP = _IOManager.IOManager_SetBroadcastIP

def IOManager_GetBroadcastIPs():
    return _IOManager.IOManager_GetBroadcastIPs()
IOManager_GetBroadcastIPs = _IOManager.IOManager_GetBroadcastIPs

def IOManager_Examine(pMsgIn, cType, fromIP, refcon):
    return _IOManager.IOManager_Examine(pMsgIn, cType, fromIP, refcon)
IOManager_Examine = _IOManager.IOManager_Examine

def IOManager_Send(*args):
    return _IOManager.IOManager_Send(*args)
IOManager_Send = _IOManager.IOManager_Send

def IOManager_Broadcast(*args):
    return _IOManager.IOManager_Broadcast(*args)
IOManager_Broadcast = _IOManager.IOManager_Broadcast

def IOManager_SetDuration(duration):
    return _IOManager.IOManager_SetDuration(duration)
IOManager_SetDuration = _IOManager.IOManager_SetDuration

def IOManager_CleanUp():
    return _IOManager.IOManager_CleanUp()
IOManager_CleanUp = _IOManager.IOManager_CleanUp

class MediaPath(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, MediaPath, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, MediaPath, name)
    __repr__ = _swig_repr

    def __init__(self, path, capacity):
        this = _IOManager.new_MediaPath(path, capacity)
        try:
            self.this.append(this)
        except __builtin__.Exception:
            self.this = this

    def path(self):
        return _IOManager.MediaPath_path(self)

    def capacity(self):
        return _IOManager.MediaPath_capacity(self)
    __swig_destroy__ = _IOManager.delete_MediaPath
    __del__ = lambda self: None
MediaPath_swigregister = _IOManager.MediaPath_swigregister
MediaPath_swigregister(MediaPath)

class MediaPaths(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, MediaPaths, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, MediaPaths, name)

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")
    __repr__ = _swig_repr

    def size(self):
        return _IOManager.MediaPaths_size(self)

    def getRandom(self):
        return _IOManager.MediaPaths_getRandom(self)

    def isGood(self):
        return _IOManager.MediaPaths_isGood(self)
    __swig_destroy__ = _IOManager.delete_MediaPaths
    __del__ = lambda self: None
MediaPaths_swigregister = _IOManager.MediaPaths_swigregister
MediaPaths_swigregister(MediaPaths)

class CLICodec(_object):
    __swig_setmethods__ = {}
    __setattr__ = lambda self, name, value: _swig_setattr(self, CLICodec, name, value)
    __swig_getmethods__ = {}
    __getattr__ = lambda self, name: _swig_getattr(self, CLICodec, name)

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined")
    __repr__ = _swig_repr
    __swig_destroy__ = _IOManager.delete_CLICodec
    __del__ = lambda self: None
    if _newclass:
        ipv4FromHost = staticmethod(_IOManager.CLICodec_ipv4FromHost)
    else:
        ipv4FromHost = _IOManager.CLICodec_ipv4FromHost
    if _newclass:
        makeSecret = staticmethod(_IOManager.CLICodec_makeSecret)
    else:
        makeSecret = _IOManager.CLICodec_makeSecret
    if _newclass:
        SetCodecsSpec = staticmethod(_IOManager.CLICodec_SetCodecsSpec)
    else:
        SetCodecsSpec = _IOManager.CLICodec_SetCodecsSpec
    if _newclass:
        GetCodecNames = staticmethod(_IOManager.CLICodec_GetCodecNames)
    else:
        GetCodecNames = _IOManager.CLICodec_GetCodecNames
    if _newclass:
        GetNamedCodec = staticmethod(_IOManager.CLICodec_GetNamedCodec)
    else:
        GetNamedCodec = _IOManager.CLICodec_GetNamedCodec
    if _newclass:
        GetCodecFromSpec = staticmethod(_IOManager.CLICodec_GetCodecFromSpec)
    else:
        GetCodecFromSpec = _IOManager.CLICodec_GetCodecFromSpec

    def getRandomMedia(self):
        return _IOManager.CLICodec_getRandomMedia(self)

    def encode(self, pMsgIn, nMsgIn, pMsgOut, nMsgOut, mediaPtr=None):
        return _IOManager.CLICodec_encode(self, pMsgIn, nMsgIn, pMsgOut, nMsgOut, mediaPtr)

    def decode(self, pMsgIn, nMsgIn, pMsgOut, nMsgOut):
        return _IOManager.CLICodec_decode(self, pMsgIn, nMsgIn, pMsgOut, nMsgOut)

    def setSecret(self, *args):
        return _IOManager.CLICodec_setSecret(self, *args)

    def isGood(self):
        return _IOManager.CLICodec_isGood(self)
CLICodec_swigregister = _IOManager.CLICodec_swigregister
CLICodec_swigregister(CLICodec)

def CLICodec_ipv4FromHost(ipStr):
    return _IOManager.CLICodec_ipv4FromHost(ipStr)
CLICodec_ipv4FromHost = _IOManager.CLICodec_ipv4FromHost

def CLICodec_makeSecret(ip1, ip2):
    return _IOManager.CLICodec_makeSecret(ip1, ip2)
CLICodec_makeSecret = _IOManager.CLICodec_makeSecret

def CLICodec_SetCodecsSpec(codecsSpec):
    return _IOManager.CLICodec_SetCodecsSpec(codecsSpec)
CLICodec_SetCodecsSpec = _IOManager.CLICodec_SetCodecsSpec

def CLICodec_GetCodecNames():
    return _IOManager.CLICodec_GetCodecNames()
CLICodec_GetCodecNames = _IOManager.CLICodec_GetCodecNames

def CLICodec_GetNamedCodec(codecName):
    return _IOManager.CLICodec_GetNamedCodec(codecName)
CLICodec_GetNamedCodec = _IOManager.CLICodec_GetNamedCodec

def CLICodec_GetCodecFromSpec(jsonSpec):
    return _IOManager.CLICodec_GetCodecFromSpec(jsonSpec)
CLICodec_GetCodecFromSpec = _IOManager.CLICodec_GetCodecFromSpec


def SetDiagPrint(func):
    return _IOManager.SetDiagPrint(func)
SetDiagPrint = _IOManager.SetDiagPrint
# This file is compatible with both classic and new-style classes.


