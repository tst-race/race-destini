#!/usr/bin/env python3

try:
    from Log import *
except:
    from datetime import datetime
    import traceback

    def logInfo (msg):          # For independent non-RiB debugging
        try:
            _dt = datetime.now ()
            print (f"{_dt.strftime ('%Y%m%d-%H:%M:%S.%f')} {msg}", flush = True)
        except:
            traceback.print_exc ()

def diagPrint (msg, logFunc = logInfo):
    logFunc (msg)


from IOManager import SetDiagPrint

SetDiagPrint (diagPrint)
