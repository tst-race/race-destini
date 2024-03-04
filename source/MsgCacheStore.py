from AbsMsgStore import AbsMsgStore

class MsgCacheStore (AbsMsgStore):

    def __init__ (self, **kwargs):

        # Initialization

        super ().__init__ (kwargs)
