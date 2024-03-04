class IsGood (object):

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
            self._isGood = False
            if _msg:
                self._err_msgs.append (_msg)

    @property
    def errorMessages (self):
        return '\n'.join (self._err_msgs) if self._err_msgs else ''

    def appendErrors (self, _obj):
        if   isinstance (_obj, __class__):
            self._isGood   &= _obj.isGood
            self._err_msgs += _obj._err_msgs

        elif isinstance (_obj, list):
            self._isGood   &= len (_obj) == 0
            self._err_msgs += _obj

        else:
            self._isGood = False
            self._err_msgs.append (_obj)


########
# main #
########

def main ():
    
    igObj = IsGood ()
    
    igObj.isGood = (True, 'As tuple')

    print (f'{igObj.isGood} {igObj.errorMessages}')


if __name__ == "__main__":
    main ()
