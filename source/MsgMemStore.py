import os

from MsgInfo import MsgInfo

from AbsMsgStore import AbsMsgStore

class MsgMemStore (AbsMsgStore):

    def __init__ (self, **kwargs):

        # Initialization

        super ().__init__ (**kwargs)

        self.uuid     = int (MsgInfo.current_posix_time ()) ^ os.getpid ()
        self._msgs    = []
        self._mhashes = set ()

    def _get_messages (self, _first, _count):
        _iFirst = max (0, _first - self.least)
        return self._msgs[_iFirst : _iFirst + _count]

    def _save_message (self, _msgInfo):
        _hDigest = _msgInfo.hexdigest

        self._msgs.append (_msgInfo)

        if _hDigest in self._mhashes:
            return False
        else:
            self._mhashes.add (_hDigest)
            return True
