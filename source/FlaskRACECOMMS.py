#!/usr/bin/env python3

from base64 import b64encode, b64decode
from datetime import datetime
import hashlib
import json
from numbers import Number
import logging
import os
from pkg_resources import resource_exists, resource_stream
import requests
import select
import signal
import sys
from threading import Thread, current_thread
import time
import traceback

# https://www.restapitutorial.com/httpstatuscodes.html

from http import HTTPStatus

from flask import Flask         # 1.0.2
from flask import request

from AbsWhiteboard import AbsWhiteboard
from DiagPrint import *
from MessageSender import MessageSender
from IOManager import *
from IPSupport import *
from MessageSender import *
from WhiteboardTransport import WhiteboardTransport

from MsgInfo import *
from MsgMemStore import MsgMemStore as MsgStore


#
# Logging
#

logDebug = logInfo


#
# Globals
#

app       = Flask (__name__)


#
# Classes
#

class _IsGood (object):

    def __init__ (self):
        super ().__init__ ()
        self._isGood   = True
        self._err_msgs = []

    @property
    def isGood (self):
        return self._isGood

    @isGood.setter
    def isGood (self, _obj):
        if isinstance (_obj, tuple):
            _new = _obj[0]
            _msg = _obj[1]
        else:
            _new = _obj
            _msg = None

        if not _new:
            self._isGood = _new
            if _msg:
                self._err_msgs.append (_msg)

    @property
    def errorMessages (self):
        return '\n'.join (self._err_msgs) if self._err_msgs else ''


class RACECOMMSRESTAPI (_IsGood):

    _RSRC_REST_API_DOC    = 'doc/README-REST_API.txt'

    _ENV_AGENT            = 'AGENT'
    _ENV_AVIDEO_SIZE      = 'AVIDEO_SIZE'
    _ENV_CONFIG           = 'CONFIG'

    _CLI_AGENT            = _ENV_AGENT.lower ()
    _CLI_CONFIG           = _ENV_CONFIG.lower ()

    _R_REG_KEY_HOST       = 'host'
    _R_REG_KEY_GROUPS     = 'groups'
    _R_REG_KEY_PEERS      = 'peers'

    _R_MGET_PAR_FIRST     = 'first'
    _R_MGET_PAR_COUNT     = 'count'

    _R_MGET_KEY_UUID      = MsgStore.KEY_UUID
    _R_MGET_KEY_LEAST     = MsgStore.KEY_LEAST
    _R_MGET_KEY_GREATEST  = MsgStore.KEY_GREATEST
    _R_MGET_KEY_MESSAGES  = 'messages'
    _R_MGET_KEY_GROUP     = 'group'
    _R_MGET_KEY_HOST      = 'host'

    _R_MPOST_PAR_GROUP    = 'group'
    _R_MPOST_PAR_DEST     = 'dest'

    _R_MPOST_KEY_ID       = MsgInfo.KEY_ID
    _R_MPOST_KEY_UUID     = MsgStore.KEY_UUID
    _R_MPOST_KEY_LEAST    = MsgStore.KEY_LEAST
    _R_MPOST_KEY_GREATEST = MsgStore.KEY_GREATEST

    _ANON_BRDCAST_IP      = '255.255.255.255'
    _ANON_BRDCAST_SPEC    = _ANON_BRDCAST_IP + ':65535'

    _MSG_SEND_TIMEOUT     = None
    _MSG_SEND_Q_BYTES     = 0

    _raceCOMMS      = None     # singleton

    _msg_store    = MsgStore ()


    @classmethod
    def singleton (cls):
        if cls._raceCOMMS is None:
            cls._raceCOMMS = cls ()

        return cls._raceCOMMS

    # https://stackoverflow.com/questions/21294889/how-to-get-access-to-error-message-from-abort-command-when-using-custom-error-ha

    class _BadRequestError (Exception):

        def __init__ (self, _h_status, _msg):
            super (__class__, self).__init__ (_h_status, _msg)

        @property
        def status (self):
            return self.args[0]

        @property
        def message (self):
            return self.args[1]

    @staticmethod
    @app.errorhandler (_BadRequestError)
    def _bad_request_handler (_bad_req):
        _rsp = app.response_class (
            response = json.dumps (_bad_req.message),
            status   = _bad_req.status,
            mimetype = 'application/json'
        )

        return _rsp

    # https://stackoverflow.com/questions/5160077/encoding-nested-python-object-in-json
    
    class _AsJSONEncoder (json.JSONEncoder):
        def default (self, obj):
            if hasattr (obj, 'asJSON'):
                return obj.asJSON ()
            else:
                return json.JSONEncoder.default (self, obj)
    
    @staticmethod
    def abort (_h_status, _msg):
        print ('abort ({}, "{}")'.format (_h_status, _msg), flush = True)
        raise __class__._BadRequestError (_h_status, _msg)

    def __init__ (self):
        super ().__init__ ()

        if self.isGood:
            self._argsDict       = vars (flask_run.get_args ())
            self._active_persona = None
            self._msgHashes      = {}
            self._hostsTo        = None
            self._hostsFrom      = None
            self._hostsBrdCast   = None
            self.wbTransport     = None
            self._avideo_size    = self._get_env (self._ENV_AVIDEO_SIZE, int, 10000)

        __class__._raceCOMMS = self

    def init (self):
        if self.isGood:
            self._active_persona = self._get_env (self._ENV_AGENT, param = self._CLI_AGENT)
            if not self._active_persona:
                self.isGood = (False, 'Missing --agent CLI argument or AGENT environment symbol')
                return self.isGood

            logDebug (f"init: I am {self._active_persona} {IPSupport.dottedIPStr (self._active_persona)}")

            IOManager.SetHostIP  (self._active_persona)
            for cType in (IOM_CT_ORDERED, IOM_CT_GENERAL, IOM_CT_AVIDEO, IOM_CT_D_SVR):
                IOManager.SetSendMsg (self._send_message, cType)
            for mType in (IOM_MT_GENERAL, IOM_MT_AVIDEO, IOM_MT_D_SVR):
                IOManager.SetProcessMsg (self._recv_message, mType)

            processMsgs = {IOM_CT_GENERAL: lambda _msg, _: IOManager.Examine (_msg, IOM_CT_GENERAL, 0, None),
                           IOM_CT_D_SVR:   lambda _msg, _: IOManager.Examine (_msg, IOM_CT_D_SVR,   0, None),
                           IOM_CT_AVIDEO:  lambda _msg, _: IOManager.Examine (_msg, IOM_CT_AVIDEO,  0, None)}

            self.wbTransport = WhiteboardTransport (self._active_persona, processMsgs)

            self._hostsTo      = HostSet (lambda: self.wbTransport.receivers)
            self._hostsFrom    = HostSet (lambda: self.wbTransport.senders)
            self._hostsBrdCast = HostSet (lambda: self._broadcastHostsPlus)

            _config = self._get_env (self._ENV_CONFIG, param = self._CLI_CONFIG)
            if not _config:
                self.isGood = (False, 'Missing --config CLI argument or CONFIG environment symbol')
                return self.isGood

            self.wbTransport.processWhiteboardSpec (_config)
            self.wbTransport.createTransports ()

            logInfo ("init returned")

        return self.isGood

    def _get_member (self, content, param, cls = str, dflt = None, env = None, optional = False):
        member = None
        if env:
            member = os.getenv (env, None)
        if member is None:
            member = content.get (param, dflt)
        else:
            param  = env

        if member is not None:
            if not isinstance (member, cls):
                try:
                    member = cls (member)
                except:
                    self.abort (HTTPStatus.BAD_REQUEST,
                                'For param "{}": {}'.format (param,
                                                             TypeError ('wanted {} but have {}'.format (cls,
                                                                                                        member.__class__))))
        elif not optional:
            self.abort (HTTPStatus.BAD_REQUEST, 'Missing param: "{}"'.format (param))

        return member

    def _get_env (self, env = None, cls = str, dflt = None, param = None, optional = True):
        return self._get_member (self._argsDict, param, cls, dflt, env, optional)

    @staticmethod
    def _debug_print (msg):
        print ('{}: {}'.format (str (datetime.now ()), msg), flush = True)

    @staticmethod
    def getRsrcStream (_path):
        try:
            if os.path.isfile (_path):
                _r_path     = open (_path, 'r')
            else:
                _pkg, _rsrc = _path.split ('/')
                _r_path     = resource_stream (_pkg, _rsrc) if resource_exists (_pkg, _rsrc) else None
    
            return _r_path
        except:
            return None

    @staticmethod
    def _send_message (to_ip, wbTransport, out_data, cType):
        try:
            diagPrint(f"_send_message: to_ip={to_ip}, cType={cType}")

            hs = IPSupport.dottedIPStr (to_ip)
            diagPrint (f"In _send_message.... {hs} -> {len (out_data)}")

            rval = wbTransport.sendMsg (hs, out_data, cType)

            if rval == IOM_PARTIAL_MSG:
                rval = 0
            elif not rval:
                diagPrint (f"send failed in _send_message: {rval}")

            return rval
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            return 0

    @staticmethod
    def _recv_message (fromIP, _refconst, in_data):
        fromIP = IPSupport.dottedIPStr (fromIP)

        diagPrint (f"_recv_mesg {fromIP} -> {len (in_data)}")
        m = hashlib.new ('ripemd160')
        m.update (in_data)
        diagPrint (f"in _recv_message {m.hexdigest ()} {len (in_data)}")

        _group = fromIP if fromIP in __class__.singleton ()._hostsBrdCast.hosts else None
        _host  = fromIP if _group is None else None
        
        if _group == __class__._ANON_BRDCAST_IP:
            _group = None

        __class__._msg_store.save_message (in_data, _group, _host)

    @staticmethod
    def hexdigest (data):
        _m = hashlib.new ('ripemd160')
        _m.update (data)

        return _m.hexdigest ()

    @property
    def _broadcastHostsPlus (self):
        _bHosts = set (self.wbTransport.broadcastHosts.keys ())
        _bHosts.add (self._ANON_BRDCAST_IP)
        
        return _bHosts

    def _process_register (self, args):

        # TODO: Currently, this is a NOOP.

        return 'OK', HTTPStatus.OK

    def _process_get_message (self, args):
        _first = self._get_member (args, self._R_MGET_PAR_FIRST, int, 0, optional = True)
        _count = self._get_member (args, self._R_MGET_PAR_COUNT, int, 1, optional = True)
        _rDict = self._msg_store.info_dict

        if _count > 0:
            _rDict[self._R_MGET_KEY_MESSAGES] = self._msg_store.get_messages (_first, _count)

        return _rDict, HTTPStatus.OK

    def _process_send_message (self, args, data):
        _msg  = None

        # Demo hack for AVIDEO
        _cType = IOM_CT_GENERAL if len (data) < self._avideo_size else IOM_CT_AVIDEO
        _cType = IOM_CT_ORDERED;

        _dest = self._get_member (args, self._R_MPOST_PAR_DEST, optional = True)
        if _dest:
            if _dest in self._hostsTo.hosts:
                _msgSender = MessageSender.messageSender (_dest, self.wbTransport, self._MSG_SEND_TIMEOUT, self._MSG_SEND_Q_BYTES)
                _status    = _msgSender.sendMessage (data, _cType, self.wbTransport)
            else:
                _msg    = f'Invalid/unknown destination: {_dest}'
                _status = -1
        else:
            _group = self._get_member (args, self._R_MPOST_PAR_GROUP, dflt = self._ANON_BRDCAST_IP)
            if _group in self._hostsBrdCast.hosts:
                _msgSender = MessageSender.messageSender (_group, self.wbTransport, self._MSG_SEND_TIMEOUT, self._MSG_SEND_Q_BYTES)
                _status    = _msgSender.sendMessage (data, _cType, self.wbTransport)
            else:
                _msg    = f'Invalid/unknown group: {_group} {self._hostsBrdCast.hosts}'
                _status = -1
            
        if _status < 0:
            if _msg is None:
                _msg = f'Internal error: {_status}'
            _rStatus = HTTPStatus.BAD_REQUEST
        
        else:
            _key    = _dest if _dest else _group
            _hashes = self._msgHashes.get (_key, None)
            if _hashes is None:
                _hashes = set ()
                self._msgHashes[_key] = _hashes

            _msg   = self._msg_store.info_dict
            _mHash = self.hexdigest (data)
            if _mHash in _hashes:
                _rStatus = HTTPStatus.ALREADY_REPORTED
            else:
                _rStatus = HTTPStatus.CREATED
                _hashes.add (_mHash)

        return _msg, _rStatus

    def _process_help (self):
        _h_rsrc = self.getRsrcStream (self._RSRC_REST_API_DOC)
        if _h_rsrc:
            _h_list = [*_h_rsrc]
            _h_rsrc.close ()
            for _i, _l in enumerate (_h_list):
                if isinstance (_l, bytes):
                    _l = _l.decode ('utf-8')
                _h_list[_i] = _l.replace ('\n', '')
            return _h_list, HTTPStatus.OK
        else:
            return 'No help available.', HTTPStatus.NO_CONTENT

    @staticmethod
    def _get_post_dict ():
        try:
            content = request.get_json (force = True)

            if isinstance (content, dict):
                return content
        except Exception as e:
            RACECOMMSRESTAPI.abort (HTTPStatus.BAD_REQUEST, 'Bad JSON input: {}'.format (e))

    @staticmethod
    def _return_response (_tup):
        return app.response_class (
            response = json.dumps (_tup[0], cls = __class__._AsJSONEncoder),
            status   = _tup[1],        # specific HTTPStatus.*
            mimetype = 'application/json'
        )

    @staticmethod
    @app.route ('/register', methods = ['POST'])
    def _route_register ():
        return __class__._return_response (
            __class__._raceCOMMS._process_register (__class__._get_post_dict ())
        )

    @staticmethod
    @app.route ('/message', methods = ['GET', 'POST'])
    def _route_message ():
        if request.method == 'POST':
            if request.content_type == 'application/octet-stream':
                _respTup = __class__._raceCOMMS._process_send_message (request.args, request.get_data ())
            else:
                _respTup = ('/message POST only accepts application/octet-stream', HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
        else:
            _respTup = __class__._raceCOMMS._process_get_message (request.args)

        return __class__._return_response (_respTup)

    @staticmethod
    @app.route ('/config/shutdown', methods = ['GET'])
    def _route_config_shutdown ():
        _werkzeug_shutdown = request.environ.get ('werkzeug.server.shutdown')
        if _werkzeug_shutdown:
            _werkzeug_shutdown ()
        else:
            os.kill (os.getppid (), signal.SIGTERM)

        return __class__._return_response (
            ('Shutting down...', HTTPStatus.OK)
        )

    @staticmethod
    @app.route ('/help', methods = ['GET'])
    def _route_help ():
        return __class__._return_response (
            __class__._raceCOMMS._process_help ()
        )


# CLI arg parsing and server invocation

#  FlaskRACECOMMS       # -c --config, -a --agent
#    <- FlaskHostPort   # -H --host, -P --port
#       <- FlaskRun     # -d --debug, run ()

from FlaskHostPort import FlaskHostPort

class FlaskRACECOMMS (FlaskHostPort):

    def __init__ (self,
                  *args,
                  **kwargs):
        super ().__init__ (*args, **kwargs)
        self._parser.add_argument ("-c", f"--{RACECOMMSRESTAPI._CLI_CONFIG}",
                                   help = f"configuration JSON file (default: %(default)s; env: {RACECOMMSRESTAPI._ENV_CONFIG})",
                                   default = None)
        self._parser.add_argument ("-a", f"--{RACECOMMSRESTAPI._CLI_AGENT}",
                                   help = f"agent host domain name (default: %(default)s; env: {RACECOMMSRESTAPI._ENV_AGENT})",
                                   default = None)

#
# Run-time
#

flask_run = FlaskRACECOMMS ()   # contains argparse results

_raceCOMMS  = RACECOMMSRESTAPI.singleton ()

if not _raceCOMMS.init ():
    _e_msg = f'RACE COMMS failure: {_raceCOMMS.errorMessages}\n'
    sys.stderr.write (_e_msg)
    _raceCOMMS.abort (HTTPStatus.NOT_IMPLEMENTED, _e_msg)


def main ():
    flask_run.run (app)


if __name__ == "__main__":
    main ()
