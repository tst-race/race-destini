from threading import RLock

from MsgInfo import MsgInfo


class AbsMsgStore (object):

    KEY_UUID     = 'uuid'
    KEY_LEAST    = 'least'
    KEY_GREATEST = 'greatest'

    def __init__ (self, **kwargs):

        # Prevent direct instantiation of this class

        _type = type (self)

        if _type == __class__:
            raise NotImplementedError ('{} may not be instantiated'.format (_type))

        # Initialization

        super ().__init__ ()

        self._lock     = RLock ()

        self._uuid     = None
        self._least    = 0
        self._greatest = 0

    @property
    def lock (self):
        return self._lock

    @property
    def next (self):
        self._greatest += 1
        
        if self.least == 0:
            self.least = 1

        return self.greatest

    @property
    def uuid (self):
        return self._uuid

    @uuid.setter
    def uuid (self, _uuid):
        self._uuid = _uuid

    @property
    def least (self):
        return self._least

    @least.setter
    def least (self, _least):
        self._least = _least

    @property
    def greatest (self):
        return self._greatest

    @greatest.setter
    def greatest (self, _greatest):
        self._greatest = _greatest

    def _get_messages (self, _first, _count):
        raise NotImplementedError (f'Must be provided by {self.__class__.__name__}!')

    def get_messages (self, _first, _count):
        if _first <= 0:
            _first = self.least
        if _count > 0 and self.least and _first >= self.least and _first <= self.greatest:
            _numMsgs = self.greatest - self.least + 1
            if _numMsgs > 0:
                with self.lock:
                   return self._get_messages (_first, min (_numMsgs, _count))
        else:
            return []
    
    def _save_message (self, _msgInfo):
        raise NotImplementedError (f'Must be provided by {self.__class__.__name__}!')

    def save_message (self, _msg, _group, _host):
        with self.lock:
            _msgInfo = MsgInfo (self.next, _msg, _group, _host)
            return self._save_message (_msgInfo)

    @property
    def info_dict (self):
        with self.lock:
            _rDict = {self.KEY_UUID: self.uuid}
            if self.least:
                _rDict.update ({self.KEY_LEAST:    self.least,
                                self.KEY_GREATEST: self.greatest})
            return _rDict
