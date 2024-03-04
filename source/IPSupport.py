import re
import socket
import struct
import hashlib
from DiagPrint import *

class IPSupport (object):

    _IPV4_REGEX = re.compile (r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')

    _ReverseDNS = {}
    

    @staticmethod
    def IP_string (ip):
        "Convert 32-bit integer to dotted IPv4 address."
        ip = socket.ntohl (ip)
        return '.'.join (map (lambda n: str (ip >> n & 0xFF), [24, 16, 8, 0]))


    @staticmethod
    def Persona_IP_string (ipObj):
        ip = __class__.IP_address(ipObj)
        ip = socket.ntohl(ip)
        return __class__.IP_string(ip)


    @staticmethod
    def IP_address_race_persona (ipObj):
        int_val = socket.ntohl(int(hashlib.sha256(ipObj.encode('utf-8')).hexdigest()[0:4], 16))
        diagPrint(f'ALERT0 PY: {ipObj} {int_val}')
        __class__._ReverseDNS[__class__.dottedIPStr(ipObj)] = ipObj
        #return socket.inet_ntoa(struct.pack('!L', int_val))
        return int_val


    @staticmethod
    def IP_address (ipObj):

        diagPrint(f'ALERT0 PY: {ipObj}')  
        "Convert numeric or domain IP string to 32-bit integer"
        if   isinstance (ipObj, int):
            return ipObj


        # https://stackoverflow.com/questions/9590965/convert-an-ip-string-to-a-number-and-vice-versa
        elif isinstance (ipObj, str):
            if ipObj.startswith("race-"):
                return IPSupport.IP_address_race_persona (ipObj)

            _ipStr = __class__.dottedIPStr (ipObj)

            if _ipStr:
                if _ipStr != ipObj:
                    __class__._ReverseDNS[_ipStr] = ipObj
                _packedIP = socket.inet_aton (_ipStr)
                return struct.unpack ("!L", _packedIP)[0]

        return None     # Error fall through


        


    @classmethod
    def ipKeySet_race_persona (cls, _host):
        _hostIn = _host
        _ipSet = set ()
        int_val = socket.ntohl(int(hashlib.sha256(_host.encode('utf-8')).hexdigest()[0:4], 16))
        diagPrint(f'ALERT1 PY: {_host} {int_val}')
        _ipSet.add(_host)
        _host = socket.inet_ntoa(struct.pack('!L', int_val))
        _ipSet.add(_host)
        __class__._ReverseDNS[_host] = _hostIn
        diagPrint(f'ALERTING RP KeySet PY: {_host} {_ipSet}')  
        return _host, _ipSet

    @classmethod
    def ipKeySet (cls, _host):

        diagPrint(f'ALERT0 KeySet PY: {_host}')
        _ipSet = set ()
                
        if isinstance (_host, int):
            _host = cls.IP_string (_host)

        if isinstance (_host, str) and _host.startswith("race-"):
            return cls.ipKeySet_race_persona (_host)

        if isinstance (_host, str) and _host.startswith("0.0."):
            _ipSet.add (_host)
            _ipSet.add (__class__._ReverseDNS[_host])
            diagPrint(f'ALERT0 Returing KeySet PY: {_host} {_ipSet}')
            return _host, _ipSet
        


        _m = cls._IPV4_REGEX.match (_host)
        if _m:
            _ipSet.add (_host)
        else:
            try:
                _hostIn = _host
                _host   = socket.gethostbyname (_hostIn)
                _ipSet.add (_hostIn)
                if _host != _hostIn:
                    __class__._ReverseDNS[_host] = _hostIn
            except:
                return None, None

            try:
                _h, _, _ipList = socket.gethostbyaddr (_host)
                _ipSet.add (_h)
                _ipSet.update (_ipList)

                # Testbed JSON hack

                _hostJson = _h.split ('.')[0]
                _         = socket.gethostbyname (_hostJson)
                _ipSet.add (_hostJson)
            except:
                pass
        diagPrint(f'ALERTING KeySet PY: {_host} {_ipSet}')  
        return _host, _ipSet        # <dotted numeric IP>, set (<IP aliases>)

    @classmethod
    def dottedIPStr (cls, _host):
        _host, _ = cls.ipKeySet (_host)

        return _host

    @classmethod
    def ipAliases (cls, _host):
        _, _alias = cls.ipKeySet (_host)

        if _alias and _host in __class__._ReverseDNS:
            _alias.add (__class__._ReverseDNS[_host])

        return _alias


class HostSet (object):
    
    def __init__ (self, hostsFunc):
        super ().__init__ ()
        self._hstFunc = hostsFunc
        self._oldSet  = set ()
        self._hosts   = None

    @property
    def hosts (self):
        _currSet = set (self._hstFunc ())
        if self._oldSet != _currSet:
            self._oldSet = _currSet
            self._hosts  = set ()

            for _host in _currSet:
                _key, _set = IPSupport.ipKeySet (_host)
                if _key and _set:
                    self._hosts.add (_host)
                    self._hosts.update (_set)

        return self._hosts
