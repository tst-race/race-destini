import json
import sys
import os
import socket
import struct

mc_gid_so_far = 0xE1000000 # 225.0.0.0
mc_groups = {}



def gen_mc_group (plist):
    global mc_gid_so_far
    plist.sort()
    idx = '|'.join(plist)
            
    if idx not in mc_groups:
        gid = socket.inet_ntoa(struct.pack('!L', mc_gid_so_far))
        mc_groups[idx] = gid
        mc_gid_so_far = mc_gid_so_far + 1
    else:
        gid = mc_groups[idx]
                
    return gid + ":"

