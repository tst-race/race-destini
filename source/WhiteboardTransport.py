#!/usr/bin/env python3

import binascii
from enum import Enum, auto
import json
import os
import random
import traceback
from threading import Lock
import uuid

from DynamicTags import DynamicTags
from DynamicPhrases import DynamicPhrases
from ImportWhiteboard import importWhiteboard
from IOManager import *
from IPSupport import IPSupport
from DiagPrint import *
from UserModel import UserModel


class AutoName (Enum):
    def _generate_next_value_ (name, start, count, last_values):
        return name


class Selection (AutoName):
    RANDOM  = auto ()
    LRU     = auto ()
    FASTEST = auto ()


class WhiteboardTransport (object):

    _KEY_TO_TRANSPORT_MAP = {'pushers': 'Pusher', 'pullers': 'Puller', 'push-pullers': 'PushPuller'}
    _DESTINATION_KEY      = 'destination'
    _PASSTHRU_CODEC_      = '"__PASSTHRU__"'

    _ANON_BRDCAST_IP      = '255.255.255.255'
    _ANON_BRDCAST_SEED    = 65535

    _singleton = None

    _KEY_S_PERSONA        = 's_persona'
    _KEY_S_TAG_SEED       = 's_tag_seed'
    _KEY_S_WHITEBOARDS    = 's_whiteboards'
    _KEY_S_TRANSPORT      = 'startTransport'

    _KEY_PERSONA          = 'persona'
    _KEY_TAG_SEED         = 'tag_seed'
    _KEY_WHITEBOARDS      = 'whiteboards'
    _KEY_PERSONA_FILTER   = 'persona_filter'
    _KEY_CREDENTIALS      = 'credentials'
    _KEY_ACCOUNT          =   'account'
    _KEY_USER_MODELS      = 'userModels'

    _KEY_TAGS             = 'tags'
    _KEY_PULLING          =   'pulling'

    @staticmethod
    def _fromDictGetDict (_dict, _key):
        if _key in _dict:
            return _dict[_key]
        else:
            _d = {}
            _dict[_key] = _d
            return _d

    @staticmethod
    def _broadcastDestTriple (_d_host):
        _parts = _d_host.split (':')
        _part0 = _parts[0]
        if len (_parts) == 2:
            _part1 = _parts[1]
            if _part1:
                _seed = int (_part1) if _part1.isdecimal () else _part1
            else:
                _seed = __class__._ANON_BRDCAST_SEED if _part0 == __class__._ANON_BRDCAST_IP else 0
        else:
            _seed  = None
        
        return _part0, IPSupport.dottedIPStr (_part0), _seed

    @staticmethod
    def _CRC32 (_arg, oldCRC = 0):
        if   isinstance (_arg, int):
            _bytes = _arg.to_bytes ((_arg.bit_length () + 7) // 8, byteorder='big')
        elif isinstance (_arg, str):
            _bytes = _arg.encode ()
        else:
            return oldCRC

        return binascii.crc32 (_bytes, oldCRC)



    def _remap_codec_map (self, _codec_map):
        from os import environ
        
        if 'ANDROID_BOOTLOGO' in environ:
            for _cdict in _codec_map.values ():
                _a_path = _cdict.get ('android_path', None)
                if _a_path:
                    _cdict['path'] = _a_path
                    
                _mdict = _cdict.get ('media', None)
                if _mdict:
                    _a_cap = _mdict.get ('android_capacities', None)
                    if _a_cap:
                        _mdict['capacities'] = _a_cap
                        
        return _codec_map


    def __init__ (self, persona, processMsgs):
#        assert self.__class__._singleton is None, 'ERROR WBT: only one instance may be created'

        self.__class__._singleton = self

        super ().__init__ ()

        self.inShutdown  = False
        self.instLock    = Lock ()      # inShutdown mutex

        self.tagSeed     = str (uuid.uuid1 ())
        self.persona     = persona
        self.aliases     = IPSupport.ipAliases (persona)
        self.processMsgs = processMsgs  # key: <channel number>, value: <process message function (_msg)>

        self.links       = {}           # key: link ID, value: link dict
        self.pullerWBs   = set ()       # list of started whiteboard pullers

        self.wbSpec      = None
        self.codecs      = []

        self.wbClasses   = {}   # key: <whiteboard module>, value: (<dict with puller, pusher, and push-puller classes>,
        #                                                           <class config dict: wbCConfig>,
        #                                                           <channel number>,
        #                                                           <codec list> or None)
        self.wbInstances = {}   # key: <whiteboard host>,   value: <wbInstance dict (key: 'class', value: <whiteboard module name>)>
        self.wbDestAccts = {}   # key: <whiteboard host>,   value: <dict (key: <destination host>, value: <user context>)>
        self.wbAccounts  = {}   # key: <whiteboard host>,   value: (<dict (key: "pushers"|"pullers"|"push-pullers",
        #                                                                  value: <dict (key: <user>, value: <credentials>)>)>,
        #                                                           <destination list>,
        #                                                           <whiteboard module>)
        self.dTransOrder = []   # [channel, ...], order of channel selection when no channel is specified (viz., cType is IOM_CT_ORDERED)
        self.dTransports = {}   # key: <channel number>,
        #                         value: <dict (key: <destination host>,
        #                                       value: <dict: (key: <whiteboard host>,
        #                                                      value: <dict (key: "Pusher"|PushPuller",
        #                                                                    value: <dict (key: <user>, value: <transport>)>)>)>)>
        self.rTransports = {}   # key: <whiteboard host>, value: <dict (key: <user>, value: <transport>)>

        self.brdcastMap  = {}   # key: <broadcast host>, value: <seed>

        self.userModels  = {}   # key: <model>, value: <dict; see UserModel.py>

        self._senders    = set ()   # senders (from)
        self._receivers  = set ()   # receivers (to)
        self._dynWBs     = {}       # dynamic whiteboards registered via transmitLink, key: whiteboard, val: transport

        self.wbTransportMap = {
            'persona':     self.persona,
            'spec':        self.wbSpec,
            'classes':     self.wbClasses,
            'userModels':  self.userModels,
            'instances':   self.wbInstances,
            'destAccts':   self.wbDestAccts,
            'accounts':    self.wbAccounts,
            'dTransOrder': self.dTransOrder,
            'dTransports': self.dTransports,
            'rTransports': self.rTransports,
            'brdcastMap':  self.brdcastMap,
            'senders':     self.senders,
            'receivers':   self.receivers
        }

    def _getMember (self, key):
        return self.wbTransportMap.get (key, None)


    def _processPersona (self, _personas, _isDict, filename):

        # 3.1.1. Find "personas:<self.persona>"

        diagPrint ("Find personas")

        _p_dict = None
        for _alias in self.aliases:
            _p_dict = _personas.get (_alias, None)
            if _p_dict:
                break

        if _p_dict is None:
            return False
        
        _p_wbs = _p_dict.get ('whiteboards', None)
        assert _isDict (_p_wbs), f'{filename}: "personas:{self.persona}" missing or bad "whiteboards"'

        # 3.1.2. Process "personas:<self.persona>:whiteboards"

        diagPrint("Process persona whiteboards")

        for _wb_host, _h_classes in _p_wbs.items ():
            _wb_known_hosts = self.wbInstances.keys ()
            assert _wb_host in _wb_known_hosts, f'{filename}: "personas:{self.persona}:whiteboards" unknown whiteboard host "{_wb_host}" (known: {_wb_known_hosts})'

            assert _isDict (_h_classes), f'{filename}: "personas:{self.persona}:whiteboards:{_wb_host}" bad value'

            _wb_dest = _h_classes.get (self._DESTINATION_KEY, [])
            assert isinstance (_wb_dest, list), f'{filename}: "persona:{self.persona}:whiteboards:{_wb_host}" bad "{self._DESTINATION_KEY}"'

            _wb_name = self.wbInstances[_wb_host]['class']

            self.wbAccounts[_wb_host] = (_h_classes, _wb_dest, _wb_name)

            _, _, _c_type, _codecs = self.wbClasses[_wb_name]
            _c_name = self.wbClasses[_wb_name][3][0]

            # Create bi-directional codecs for multicast hosts and remote peers

            for _d_host in _wb_dest:
                _host, _dest, _seed = self._broadcastDestTriple (_d_host)
                if _seed is None:
                    self._makeUnicastCodecs   (_dest, _c_type, _c_name)
                else:
                    self._makeMulticastCodecs (_host, _c_type, _c_name, _seed, _dest)

                diagPrint (f"After calling MakeCodecs {_host} {_dest}")

         #   diagPrint("done bidirectional")

        # 3.2. For "personas:<persona>", create whiteboard-centric user context
        #      map (key: "<whiteboard host>", value: <dict (key: <persona>", value: <user context>)>)

        for _persona, _p_dict in _personas.items ():
            _p_wbs = _p_dict.get ('whiteboards', None)
            assert isinstance (_p_wbs, dict), f'ERROR: persona "{_persona}" is missing "whiteboards"'

            for _wb_host, _h_classes in _p_wbs.items ():
                #diagPrint (f"_wb_host = {_wb_host}")
                _dUContext  = self._makeUserContext (_h_classes)
                _personaIP  = IPSupport.dottedIPStr (_persona)
                _wb_d_accts = self._fromDictGetDict (self.wbDestAccts, _wb_host)
                _wb_d_accts[_persona]   = _dUContext
                _wb_d_accts[_personaIP] = _dUContext

                _wb_dest = _h_classes.get (self._DESTINATION_KEY, [])
                assert isinstance (_wb_dest, list), f'{filename}: "persona:{_persona}:whiteboards:{_wb_host}" bad "{self._DESTINATION_KEY}"'
                if _persona == self.persona:
                    #diagPrint (f"dUcontext = {_dUContext}")
                    _tags        = _dUContext.get ('tags', None)
                    self.tagSeed = _tags.get ('pulling', None) if _tags else None

                # Search for and save senders

                for _d_host in _wb_dest:
                    #diagPrint (f"_d_host = {_d_host}")
                    _, _dest, _seed = self._broadcastDestTriple (_d_host)
                    if _seed is None and _dest in self.aliases:
                        self._senders.update (IPSupport.ipAliases (_persona))
                        break

        return True

    def processWhiteboardSpec (self, filename):
        _retVal = False
        _isDict = lambda _o: isinstance (_o, dict)       # convenience "macro": checks if argument is a dict
        _isList = lambda _o: isinstance (_o, list)       # convenience "macro": checks if argument is a list

        # Create a channel key map (dict (key: "IOM_CT_*" | <channel int>, value: <channel int>))

        _channelKeys = dict (filter (lambda _e: _e[0].startswith ('IOM_CT_') and _e[1] >= 0, dict (globals ()).items ()))
        _channelKeys.update ({_v: _v for _v in _channelKeys.values ()})

        with open (filename, "r") as f_in:

            # 0. Load and check JSON whiteboard file

            diagPrint("Loading and checking JSON whiteboard file")

            _spec = json.load (f_in)
            assert _isDict (_spec), f'{filename} does not contain a top-level dict'

            self.wbSpec = _spec
            
            # 1. Process "codecs" entries

            diagPrint ("Processing codec entries")
            
            _codecs = _spec.get ('codecs', {})

            if _codecs:
                self._remap_codec_map (_codecs)
                assert _isDict (_codecs) and CLICodec.SetCodecsSpec (json.dumps (_codecs)), f'{filename}: missing or bad "codecs" entry'
                self.codecs = list (_codecs.keys ())

            # 2. Process "whiteboards" entries

            diagPrint ("Process whiteboard entries")

            _whiteboards = _spec.get ('whiteboards', None)
            assert _isDict (_whiteboards), f'{filename}: missing or bad "whiteboards" entry'

            # 2.1. Process "whiteboards:classes"

            diagPrint ("Process whiteboard classes")

            _cls = _whiteboards.get ('classes', None)
            assert _isDict (_cls), f'{filename} "whiteboards": bad or missing "classes" entry'

            _ch_key_set = set ()        # for comparison against the "channel order" list

            for _c_name, _cconfig in _cls.items ():
                diagPrint (f'Before importWhiteboard {_c_name}')
                _wbClasses = importWhiteboard (_c_name)
                diagPrint (f'After importWhiteboard {_c_name}')
                assert _wbClasses, f'{filename}: "{_c_name}" whiteboard implementation not found.'

                _channel    = _cconfig.get ('channel', None)
                _channelOut = _channelKeys.get (_channel, None)
                assert isinstance (_channelOut, int), f'{filename}: "{_c_name}" whiteboard bad or missing "channel" key ({_channel})'

                _wbCodecs   = _cconfig.get ('codecs', None)
                if _wbCodecs:
                    assert _isDict (_codecs),   f'{filename}: missing "codecs" entry'
                    assert _isList (_wbCodecs), f'{filename}: "{_c_name}" whiteboard bad "codecs" value ({_wbCodecs})'

                    for _wbC in _wbCodecs:
                        assert _codecs.get (_wbC, None) is not None, f'{filename}: "{_c_name}" whiteboard unknown "codec" ({_wbC})'
                else:
                    _wbCodecs   = [self._PASSTHRU_CODEC_]

                _channelKeys['channel'] = _channelOut
                self.wbClasses[_c_name] = (_wbClasses, _cconfig, _channelOut, _wbCodecs)

                _ch_key_set.add (_channelOut)

            # 2.2. Process "whiteboards:channel order"

            diagPrint ("Process whiteboard channel order")

            _ch_order = _whiteboards.get ('channel order', None)
            assert isinstance (_ch_order, list), f'{filename}: "whiteboards": bad or missing "channel order" entry'

            _ch_order_out = list (map (lambda _k: _channelKeys.get (_k, None), _ch_order))
            assert None not in _ch_order_out, f'{filename}: "whiteboards": bad "channel order" element ({_ch_order})'

            _whiteboards['channel order'] = _ch_order_out

            _ch_order_set = set (_ch_order_out)

            _ch_delta = _ch_key_set ^ _ch_order_set
            assert len (_ch_delta) == 0, f'{filename}: "whiteboards": "channel order" and whiteboard channels mismatch - ({_ch_delta} not found)'

            self.dTransOrder = _ch_order_out
            
            for _cType in self.dTransOrder:
                IOManager.AddChannel (_cType);

            # 2.3. Process "whiteboards:userModels"

            diagPrint ("Process whiteboards: userModels")

            _userModels = _whiteboards.get ('userModels')
            assert _isDict (_userModels), f'{filename}: "whiteboards": bad or missing "userModels" entry'

            for _userModel, _umDict in _userModels.items ():
                assert _isDict (_umDict), f'{filename}: "whiteboards:userModels" {_userModel}, missing or bad instance dict'

                _um = UserModel (_umDict)
                assert _um.isGood, _um.errorMessages

            self.userModels = _userModels

            # 2.4. Process "whiteboards:instances"

            diagPrint ("Process whiteboards: instances")

            _insts = _whiteboards.get ('instances', None)
            assert _isDict (_insts), f'{filename}: "whiteboards": bad or missing "instances" entry'

            for _wb_host, _wbInstance in _insts.items ():
                assert _isDict (_wbInstance), f'{filename}: "whiteboards:instances" {_wb_host}, missing or bad instance dict'

                _c_name = _wbInstance.get ('class', None)
                assert _c_name in self.wbClasses.keys (), f'{filename}: "whiteboards:instances" {_wb_host}, missing or unknown whiteboard module class "{_c_name}"'

                # 2.4.1. Process "credentials:account"

                _creds = _wbInstance.get (self._KEY_CREDENTIALS, None)
                if isinstance (_creds, dict):
                    _account = _creds.get (self._KEY_ACCOUNT, None)
                    if _account:
                        _personaFilter = _creds.get (self._KEY_PERSONA_FILTER, None)
                        _persona       = eval (_personaFilter) (self.persona) if _personaFilter else self.persona
                        _creds[self._KEY_ACCOUNT] = _account.replace ('{persona}', _persona)

                # 2.4.2. Process "userModel"

                _userModel = _wbInstance.get ('userModel')
                assert _userModel is None or _userModel in self.userModels, f'{filename}: "whiteboards:userModel" {_wb_host}, unknown userModel "{_userModel}"'

                if _userModel:
                    _wbInstance['userModel'] = self.userModels[_userModel]

                # Add instance only if the host is DNS resolvable (could also add reachability check).
                if IPSupport.IP_address (_wb_host):
                    self.wbInstances[_wb_host] = _wbInstance

            # 3. Process "personas"

            diagPrint ("Process personas")

            _personas = _spec.get ('personas', None)

            if _personas:
                _retVal = self._processPersona (_personas, _isDict, filename)

                #assert _isDict (_p_dict), f'{filename}: "personas" does not contain "{self.persona}"'

                # TODO: validate pullers and pushers?

        # Provisionally initialize DynamicTags

        _tagsFile = os.path.join (os.path.dirname (filename), 'wordlist.txt')
        if os.path.exists (_tagsFile):
            diagPrint (f"loading wordlist")
            DynamicTags.Initialize (_tagsFile)

        _phraseFile = os.path.join (os.path.dirname (filename), 'phrases.txt')
        if os.path.exists (_phraseFile):
            diagPrint (f"loading phraselist")
            DynamicPhrases.Initialize (_phraseFile)

        return _retVal 

    def addInstance (self, _wb_host, _wbInstance):
        self.wbInstances[_wb_host] = _wbInstance

    def pullingTag (self, _wb_host, _dest, _tagIn):

        def _getDictVal (_dictIn, _key, _default = None):
            _valOut = _dictIn.get (_key, {})
            if not _valOut:
                _valOut = _default if _default else _valOut
                _dictIn[_key] = _valOut

            return _valOut


        _u_contexts  = _getDictVal (self.wbDestAccts, _wb_host)
        _userContext = _getDictVal (_u_contexts,      _dest)
        _tags        = _getDictVal (_userContext,     self._KEY_TAGS)
        _pulling     = _getDictVal (_tags,            self._KEY_PULLING, _tagIn)
        
        _wb_IP                   = IPSupport.dottedIPStr (_wb_host)
        self.wbDestAccts[_wb_IP] = _u_contexts

        _parts = _dest.split (':')
        _dest_IP                 = IPSupport.dottedIPStr (_dest if len (_parts) == 1 else _parts[0]) + ('' if len (_parts) == 1 else ':')
        _u_contexts[_dest_IP]    = _userContext
        
        diagPrint (f"WhiteboardTransport: pullingTag: wb_host = {_wb_host}, dest = {_dest}, tagIn = {_tagIn}")
        diagPrint (f"WhiteboardTransport: pullingTag: wbIP = {_wb_IP} wbhost = {_wb_host} destIP = {_dest_IP}")
        diagPrint (f"destaccounts = {self.wbDestAccts}")
        return _pulling

    def _makeUnicastCodecs (self, _dest, _c_type, _c_name):
        self._receivers.update (IPSupport.ipAliases (_dest))

        diagPrint (f"Calling MakeCodecs unicast {_dest} {_c_type} {_c_name}")
        IOManager.MakeCodecs (IPSupport.Persona_IP_string(_dest), _c_type, _c_name)
        
    def _makeMulticastCodecs (self, _host, _c_type, _c_name, _seed, _dest):
        self.brdcastMap[_host] = _seed
        self.brdcastMap[_dest] = _seed

        _secret = self._CRC32 (_seed, self._CRC32 (_host))

        diagPrint (f"Calling MakeCodecs multicast {_dest} {_c_type} {_c_name}")
        IOManager.MakeCodecs (_dest, _secret, _c_type, _c_name)

    def makeCodecs (self, _dest, _isMulticast = False, _seed = 0):
        _count = -1

        # Validate that the destination corresponds to a known persona

        for _destAcct in self.wbDestAccts.values ():
            if _dest in _destAcct:
                _count = 0
                break

        if _count != 0:
            diagPrint (f"ERROR: makeCodecs ({_dest}, {_isMulticast}): unknown persona ({_dest})")
            return _count

        # Provisionally append the persona as a destination and create
        # its associated codecs.

        for _, _wb_dest, _wb_name in self.wbAccounts.values ():
            if _dest in _wb_dest:
                continue    # peer already registered

            # New peer

            _wb_dest.append (_dest)

            # Determine associated channel type and codec name

            _, _, _c_type, _codecs = self.wbClasses[_wb_name]
            _c_name = _codecs[0]

            # Create bi-directional codecs for multicast hosts and remote peers

            if _isMulticast:
                _destIP = IPSupport.dottedIPStr (_dest)
                self._makeMulticastCodecs (_dest, _c_type, _c_name, _seed, _destIP)
            else:
                self._makeUnicastCodecs   (_dest, _c_type, _c_name)

            _count += 1

        return _count


    # Extract the user context from the persona host dict

    def _makeUserContext (self, _h_classes):
        _transportKeys = self._KEY_TO_TRANSPORT_MAP.keys ()
        _ucontext      = {}

        for _key, _val in _h_classes.items ():

            # Ignore transport keys

            if _key not in _transportKeys and _key != self._DESTINATION_KEY:
                _ucontext[_key] = _val

        return _ucontext

    # Create transports and populate the destination transport dict
    # (key: destination, value: host-based pushers and pullers) and
    # the requester transport dict (key: whiteboard host, value:
    # user-based pullers).

    def createTransports (self, start_pullers = True):
        for _wb_host, _acc_tuple in self.wbAccounts.items ():
            _h_classes, _wb_dest, _wb_module = _acc_tuple
            _user_ctxt  = self._makeUserContext (_h_classes)
            _tags       = _user_ctxt.get ('tags', None)
            _wbInstance = self.wbInstances[_wb_host]
            _wbClasses, _wbCConfig, _channel, _codecs = self.wbClasses[_wb_module]

            _processMsg = self.processMsgs[_channel]

            #for _t_type in self._KEY_TO_TRANSPORT_MAP.values ():

            diagPrint (f"WhiteboardTransport: createTransports {_wb_host} {_acc_tuple} {_wbInstance}")

        for brdcastHost, brdcastSeed in self.broadcastHosts.items ():
            IOManager.SetBroadcastHost (brdcastHost, brdcastSeed)

    @property
    def broadcastHosts (self):
        return self.brdcastMap

    @property
    def senders (self):
        return self._senders

    @property
    def receivers (self):
        return self._receivers

    def _startTransport (self, _wb_host, _t_type, _user, _tagSeed, _wb_dest, _creds = {}, _oldTransport = None):

        _wbInstance = self.wbInstances.get (_wb_host, None)
        diagPrint (f"WhiteboardTransport: _startTransport: Entering startTransport {_wb_host} {_t_type} {_user} {_tagSeed} {_wb_dest} {_wbInstance}")
        
        if _t_type == 'Puller':
            if _wb_host in self.pullerWBs:
                diagPrint (f"returning from startTransport because puller {_wb_host} exists")
                return True, None
            else:
                self.pullerWBs.add (_wb_host)
        
        if _wbInstance:
            _wb_module  = _wbInstance['class']
            _tuple      = self.wbClasses[_wb_module]
            _wbClasses, _wbCConfig, _channel, _codecs = _tuple
            _processMsg = self.processMsgs[_channel]
            _pp_trans   = None

            _pp_class   = _wbClasses.get (_t_type, None)
            if _pp_class:

                # Conditionally create Puller, Pusher, or PushPuller transport

                if not _oldTransport or _t_type != 'Pusher':
                    try:
                        _pp_trans = _pp_class (_user, _creds, _tagSeed, _wbInstance, _wbCConfig)
                    except Exception as e:
                        diagPrint (f"Error creating _pp_trans {e} {traceback.print_exc()}")
                        return False, None
                
                    # Define the codecs
                    
                    _pp_trans.defineCodecs (self.channelCodecs (_channel))

                # Make ourself and our members accessible
                if _pp_trans:
                    _pp_trans._setWBTransport (self, self._getMember)

                # For Pullers, set the process message callback

                if _t_type != 'Pusher':
                    _pp_trans.setProcessMsg (_processMsg)

                    # Populate the receiver transport map

                    _dest_wb = self._fromDictGetDict (self.rTransports, _wb_host)
                    _dest_wb[_user] = _pp_trans

                    # Start the puller

                    _pp_trans.start ()

                # Populate the destination transport map used by sendMsg ()

                if _t_type != 'Puller':
                    for _d_host in _wb_dest:
                        _, _dest, _ = self._broadcastDestTriple (_d_host)
                        _chann_wbs  = self._fromDictGetDict (self.dTransports, _channel)
                        _dest_wb    = self._fromDictGetDict (_chann_wbs, _dest)
                        _transports = self._fromDictGetDict (_dest_wb, _wb_host)
                        _transport  = self._fromDictGetDict (_transports, _t_type)
                        if _oldTransport:
                            _pp_trans = _oldTransport
                        _transport[_user] = _pp_trans

            return True, _pp_trans

        return False, None

    def _makeDynCodecs (self, _d_host, _wbHost):
        # Determine associated channel type and codec name

        diagPrint (f"In makeDynCodecs: dest = {_d_host}, _wbHost = {_wbHost}")
        diagPrint (f"In makeDynCodecs: wbclasses = {self.wbClasses}")
        diagPrint (f"In makeDynCodecs: wbInstances = {self.wbInstances}")

        _wbInst = self.wbInstances[_wbHost]
        _whiteboard = _wbInst['class']
        
        _, _, _c_type, _codecs = self.wbClasses[_whiteboard]
        _c_name = _codecs[0]

        diagPrint (f"In makeDynCodecs: _c_type = {_c_type}, _c_name = {_c_name}, whiteboard = {_whiteboard}") 

        # Create bi-directional codecs for remote peers

        _host, _dest, _seed = self._broadcastDestTriple (_d_host)
        if _seed is None:
            self._makeUnicastCodecs   (_dest, _c_type, _c_name)
        else:
            self._makeMulticastCodecs (_host, _c_type, _c_name, _seed, _dest)

    def _receiveLink (self, linkID, _s_persona, _s_pullingTag, _filter = None, _doGenesis = False):
        linkDict = self.links.get (linkID)
        
        if linkDict is None:

            # Create puller
            
            _wb_hosts = list (self.wbInstances.keys ())
            if _wb_hosts:
                _s_wb_hosts = _wb_hosts
                for _wb_host in _wb_hosts:
                    self._makeDynCodecs (_s_persona, _wb_host)
                    # self._startTransport (_wb_host, 'Puller', _s_persona, _s_pullingTag, [_s_persona])

                # Provisionally filter the whiteboard host list (viz., for Pixelfed-DASH plug-in)

                if _filter:
                    diagPrint (f'_wb_hosts = {_wb_hosts} filter = {_filter}')
                    _wb_hosts = list (filter (_filter, _wb_hosts))
                    diagPrint (f'_wb_hosts = {_wb_hosts}')

                # Determine the tag seed, accommodating Genesis link definitions
                if _doGenesis:
                    _pullingTag = None
                    for _wb_host in _wb_hosts:
                        _pullingTag = self.pullingTag (_wb_host, _s_persona, _s_pullingTag)
                        if _pullingTag != _s_pullingTag:     # Genesis link pulling tag takes precedence
                            break
                else:
                    _pullingTag = _s_pullingTag

                linkDict = {self._KEY_PERSONA:       self.persona,
                            self._KEY_TAG_SEED:      _pullingTag,
                            self._KEY_WHITEBOARDS:   _wb_hosts,
                            self._KEY_S_PERSONA:     _s_persona,
                            self._KEY_S_TAG_SEED:    _s_pullingTag,
                            self._KEY_S_WHITEBOARDS: _s_wb_hosts,
                            self._KEY_S_TRANSPORT:   True}
                self.links[linkID] = linkDict

        return linkDict

    def receiveLink (self, linkID, _filter = None):
        return self._receiveLink (linkID, self.persona, self.tagSeed, _filter, _doGenesis = True)

    def receiveLinkFromAddress (self, linkID, _persona, _pullingTag, _filter = None):
        return self._receiveLink (linkID, _persona,     _pullingTag,  _filter, _doGenesis = False)

    def startReceiveLink (self, linkID):
        linkDict = self.links.get (linkID)
        
        if linkDict and linkDict[self._KEY_S_TRANSPORT]:
            linkDict[self._KEY_S_TRANSPORT] = False

#            _s_persona    = linkDict[self._KEY_S_PERSONA]
#            _s_pullingTag = linkDict[self._KEY_S_TAG_SEED]
#            _s_wb_hosts   = linkDict[self._KEY_S_WHITEBOARDS]

            _persona    = linkDict[self._KEY_PERSONA]
            _pullingTag = linkDict[self._KEY_TAG_SEED]
            _wb_hosts   = linkDict[self._KEY_WHITEBOARDS]


            for _wb_host in _wb_hosts:
                #self._startTransport (_wb_host, 'Puller', _s_persona, _s_pullingTag, [_s_persona])
                self._startTransport (_wb_host, 'Puller', _persona, _pullingTag, [_persona])

            return True
        else:
            return False

    def transmitLink (self, linkDict, _filter = None):
        _user        = linkDict.get (self._KEY_PERSONA,    None)
        _tagSeed     = linkDict.get (self._KEY_TAG_SEED,   None)
        _whiteboards = linkDict.get (self._KEY_WHITEBOARDS, None)

        diagPrint(f"transmitLink called: {_user}, {_tagSeed}, {_whiteboards}")

        if _user and _tagSeed and _whiteboards:
            _a_wbs = set (_whiteboards) | set (self.wbInstances.keys ())
            _l_wbs = set (filter (_filter, _a_wbs) if _filter else _a_wbs) 
            _r_wbs = set (_a_wbs) - _l_wbs
            diagPrint (f"transmitLink: l_wbs = {_l_wbs} r_wbs = {_r_wbs}")
            
            for _l_wb in _l_wbs:
                for _r_wb in _r_wbs:
                    _ = self.pullingTag (_l_wb, _r_wb, _tagSeed)

            if len (_r_wbs) == 0:
                _ = self.pullingTag (_l_wb, _user, _tagSeed)
                
            for _whiteboard in _whiteboards:
                self._makeDynCodecs (_user, _whiteboard)

                _oldTransport = self._dynWBs.get (_whiteboard, None)
                _status, _newTransport = self._startTransport (_whiteboard, 'Pusher',
                                                               self.persona, _tagSeed, [_user],
                                                               _oldTransport = _oldTransport)
                if _oldTransport != _newTransport:
                    self._dynWBs[_whiteboard] = _newTransport
                    
    def _getWhiteboards (self, dest, cType):
        _ch  = None
        _wbs = None

        # A specific channel was requested

        if cType != IOM_CT_ORDERED:
            _dTransport = self.dTransports.get (cType, None)
            if _dTransport:
                _ch  = cType
                _wbs = _dTransport.get (dest, None)

        # Search through the specified channel order

        else:
            for _ch in self.dTransOrder:
                _dTransport = self.dTransports.get (_ch, None)
                if _dTransport:
                    _wbs = _dTransport.get (dest, None)

                    # Found destination whiteboards

                    if _wbs:
                        #diagPrint (f'_getWhiteboards: {self.dTransOrder} {_ch} {dest} {_wbs}')
                        cType = _ch
                        break

        return _ch, _wbs
    

    def broadcast (self, msg, cType, host_selection = Selection.RANDOM, pp_selection = Selection.RANDOM):
        status = len (self.brdcastMap) > 0

        for _brdcastHost in self.brdcastMap.keys ():
            status &= self.sendMsg (_brdcastHost, cType, host_selection, pp_selection)

        return status

    def senderFor (self, dest, cType = IOM_CT_ORDERED, host_selection = Selection.RANDOM, pp_selection = Selection.RANDOM, _whiteboards = None):
        with self.instLock:
            if self.inShutdown:
                diagPrint(f'ERROR: In shutdown mode.... should not happen')
                return None, None

        _sender      = None
        _userContext = None

        if self.dTransports:
            host_selection = host_selection if host_selection in list (Selection) else Selection.RANDOM
            pp_selection   = pp_selection   if host_selection in list (Selection) else Selection.RANDOM

            # Find/select a Pusher

            _ch, whiteboards = self._getWhiteboards (dest, cType)
            if isinstance (whiteboards, dict):

                # Get whiteboard hosts

                _wb_hosts = _whiteboards if _whiteboards else list (whiteboards.keys ())

                # diagPrint (f'senderFor ({dest}, {_ch}): {whiteboards}')

                while _wb_hosts:

                    # TODO: implement LRU and FASTEST

                    if host_selection == Selection.RANDOM or True:
                        _idx = random.randrange (len (_wb_hosts))

                    _wb_host      = _wb_hosts.pop (_idx)
                    _rnd_host_val = whiteboards[_wb_host]

                    # Fetch destination user context

                    _u_contexts = self.wbDestAccts.get (_wb_host, {})
                    diagPrint (f"senderFor: wbDestAccts = {self.wbDestAccts}")
                    
                    assert isinstance (_u_contexts, dict), f'ERROR: no destination accounts for "{_wb_host}"'

                    _userContext = _u_contexts.get (dest, {})

                    diagPrint (f'senderFor: _wb_host = {_wb_host}, dest = {dest}, _u_contexts = {_u_contexts} _userContext = {_userContext}')

                    if _ch == IOM_CT_D_SVR:
                        _userContext = _userContext if _userContext is not None else {}
                    else:
                        assert isinstance (_userContext, dict), f'ERROR: no user context for "{_wb_host}:{dest}"'

                    _pushers = list (_rnd_host_val.keys ())

                    while _pushers:

                        # TODO: implement LRU and FASTEST

                        if pp_selection == Selection.RANDOM or True:
                            _idx = random.randrange (len (_pushers))

                        _push_val   = _rnd_host_val[_pushers.pop (_idx)]

                        _push_trans = list (_push_val.values ())

                        while _push_trans:

                            # TODO: implement LRU and FASTEST

                            if pp_selection == Selection.RANDOM or True:
                                _idx = random.randrange (len (_push_trans))

                            _push_transport = _push_trans.pop (_idx)


                            # Provisionally start the transport

                            if not _push_transport.is_alive ():
                                _push_transport.start ()

                            # Provisionally return the sender
                            if _push_transport.is_alive () :
                                _sender = _push_transport
                            else:
                                diagPrint(f'ERROR: senderFor push tranport is not alive... returning none for _sender') 
                                _sender = None

                            if _sender:
                                break

                        if _sender:
                            break

                    if _sender:
                        break
            else:
                diagPrint(f"ERROR: WhiteboardTransport:senderFor No whiteboard for {dest} {cType}")
        else:
            diagPrint (f"ERROR: WhiteboardTransport:senderFor No dTransports")
            
        return _sender, _userContext

    def channelCodecs (self, cType):
        wb_classes = list (self.wbClasses.values ())
        for _, _, _channel, _codecs in wb_classes:

            # Given cType, search for codecs
        
            if _channel == cType:
                if _codecs:
                    return _codecs
                break
        
        return None
    
    def sendMsg (self, dest, msg, cType, host_selection = Selection.RANDOM, pp_selection = Selection.RANDOM):
        _sender, _userContext = self.senderFor (dest, cType, host_selection, pp_selection)

        diagPrint(f'In Whiteboard Transport sendMsg {dest} {cType} {_sender}')
        
        if _sender:
            return _sender.pushMsg (msg, dest, _userContext)
        else:
            return False

    def flush (self):
        if not self.inShutdown:

            # Flush pusher transports
    
            for _destWbs in self.dTransports.values ():         # <channel number> values
                for _wbTrans in _destWbs.values ():             # <destination host> values
                    for _ppTrans in _wbTrans.values ():         # <whiteboard host> values
                        for _userTrans in _ppTrans.values ():   # "Pusher"|"PushPuller" values
                            for _trans in _userTrans.values (): # <user> values
                                if _trans._channel:
                                    _trans.notify ()

    def shutdown (self):
        if not self.inShutdown:
            self.flush ()

            with self.instLock:
                self.inShutdown = True

            # Close pusher transports

            for _destWbs in self.dTransports.values ():         # <channel number> values
                for _wbTrans in _destWbs.values ():             # <destination host> values
                    for _ppTrans in _wbTrans.values ():         # <whiteboard host> values
                        for _userTrans in _ppTrans.values ():   # "Pusher"|"PushPuller" values
                            for _trans in _userTrans.values (): # <user> values
                                if _trans._channel:
                                    _trans._closeChannel ()

            # Close puller transports

            for _userTrans in self.rTransports.values ():       # <whiteboard host> values
                for _trans in _userTrans.values ():             # <user> values
                    if _trans._channel:
                        _trans._closeChannel ()


def main ():
    _test = WhiteboardTransport ('race-server-2', {IOM_CT_GENERAL: lambda _x: _x, IOM_CT_D_SVR: lambda _x: _x})
#    _test.processWhiteboardSpec ('../config/whiteboard.json')
    _test.processWhiteboardSpec ('../../../dash-config/whiteboard.json')
    _test.createTransports (False)

    WhiteboardTransport ('<bad request: ask for another instance>', None)


if __name__ == "__main__":
    main ()
