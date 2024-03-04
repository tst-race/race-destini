import os
import time
import threading

# The model: Only the receiver can remove a file.  Sender has to wait
# until the file is gone before sending the next line.

# This is nullchat, which uses /tmp files for holding messages:


class NullChat:
    def __init__(self, tmpdir="/tmp/", dir=None, user='user1', reverse=False, verbose=False):
        self.verbose = verbose
        self.pid = os.getuid()
        self.sleep_range = (1,1)
        if reverse:
            self.outbound = f"/tmp/chat_i"
            self.inbound =  f"/tmp/chat_o"
        else:
            self.outbound = f"/tmp/chat_o"
            self.inbound =  f"/tmp/chat_i"
        self.titles = []
        self.wbname = "null"

    def write(self, string):
        with open(self.outbound, 'w') as f:
            f.write(string)
        return True

    def read(self):
        out = None
        try:
            with open(self.inbound, 'r') as f:
                out = f.read()
        except:
            pass
        return out

    def wait_for_response(self, which, max_iter=100, sleeptime=1):
        info = os.stat(self.inbound)
        cur = into.st_mtime
        return cur

    def send(self, string):
        while os.path.exists(self.outbound):
            time.sleep(0.5)
        result = self.write(string)
        while not result:
            result = self.write(string)

    def receive(self):
        out = None
        out = self.read()
        if out is not None:
            os.remove(self.inbound)
        return out

    def close(self):
        return
