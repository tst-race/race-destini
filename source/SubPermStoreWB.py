import PermStoreWB

class Whiteboard (PermStoreWB.Whiteboard):

    def __init__ (self, user, credentials, userContext, wbInstance, wbCConfig):

        super ().__init__ (user, credentials, userContext, wbInstance, wbCConfig)
