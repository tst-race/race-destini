#!/usr/bin/env python3

import sys

from DiagPrint import diagPrint


# importWhiteboard: imports and returns a named WBPushPullers implementation
#
# Argument: whiteboard module name (string)
# Returns:  a map of a whiteboard's Puller, Pusher, and PushPuller
#           transport classes

def importWhiteboard (wb_modname):

    # https://stackoverflow.com/questions/3012473/how-do-i-override-a-python-import

    # "Inject" a concrete Whiteboard base class implementation

    sys.modules['Whiteboard'] = __import__ (wb_modname)

    # Instantiate whiteboard module and import its classes

    from WBPushPullers import Puller, Pusher, PushPuller

    # Save the whiteboard classes in a map

    _locals     = locals ()
    _wb_classes = ('Puller', 'Pusher', 'PushPuller')

    _wbDict     = {}

    for _wb_cname in _wb_classes:
        _wb_class = _locals.get (_wb_cname, None)
        if _wb_class:
            _wbDict[_wb_cname] = _wb_class

    # Remove instantiated whiteboard module

    del sys.modules['WBPushPullers']

#    diagPrint (f'importWhiteboard ({wb_modname}): {_wbDict}')

    return _wbDict


def _debugPrint (_transports):
    for _key, _value in _transports.items ():
        print ('{}: {} ({})'.format (_key, _value, _value.__bases__))

    return _transports


def main ():
    _pfTransports = _debugPrint (importWhiteboard ('Pixelfed'))
    _dsTransports = _debugPrint (importWhiteboard ('DashSvr'))


if __name__ == '__main__':
    main ()
