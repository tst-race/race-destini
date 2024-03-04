
# https://stackoverflow.com/questions/8777753/converting-datetime-date-to-utc-timestamp-in-python

import base64
from datetime import datetime, timezone, timedelta
import hashlib


class MsgInfo (object):

    KEY_ID = 'id'
    
    _dt_utc  = datetime (1970, 1, 1, tzinfo = timezone.utc)
    _t_del_1 = timedelta (seconds = 1)
    
    @staticmethod
    def _datetime_to_posix (_dt):
        return (_dt - __class__._dt_utc) / __class__._t_del_1

    @staticmethod
    def current_posix_time ():
        return __class__._datetime_to_posix (datetime.now (tz = timezone.utc))

    def __init__ (self, _id, _msg, _group = None, _host = None):

        # Initialization

        super ().__init__ ()

        self._id     = _id
        self._c_date = self.current_posix_time ()
        self._msg    = _msg
        self._group  = _group
        self._host   = _host if _group is None else None

    @property
    def id (self):
        return self._id

    @id.setter
    def id (self, _id):
        self._id = _id

    @property
    def msg (self):
        return self._msg

    @property
    def group (self):
        return self._group

    @property
    def host (self):
        return self._host

    @property
    def hexdigest (self):
        _m = hashlib.new ('md5')
        _m.update (self._msg)

        return _m.hexdigest ()

    def asJSON (self):

        _jsonDict = {'message': base64.b64encode (self.msg).decode ("utf-8")}

        for _attr in ('id', 'group', 'host'):
            _val = getattr (self, f'_{_attr}')
            if _val is not None:
                _jsonDict[_attr] = _val

        return _jsonDict
