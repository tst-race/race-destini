"""
"""
# /usr/bin/env/python3


from base64 import b64encode, b64decode
import json
import os
import requests
import socket
import threading
import time
import traceback
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# RACE Libraries

from commsPluginBindings import (
    EncPkg,
    IRacePluginComms,
    IRaceSdkComms,
    LinkProperties,
    LinkPropertyPair,
    LinkPropertySet,
    PluginConfig,
    RACE_BLOCKING,
    RACE_UNLIMITED,
    CONNECTION_CLOSED,  # ConnectionStatus
    CONNECTION_UNAVAILABLE,  # ConnectionStatus
    CONNECTION_OPEN,  # ConnectionStatus
    NULL_RACE_HANDLE,  # RaceHandle
    PACKAGE_FAILED_GENERIC,  # PackageStatus
    PACKAGE_SENT,  # PackageStatus
    PLUGIN_ERROR,  # PluginResponse
    PLUGIN_FATAL,  # PluginResponse
    PLUGIN_OK,  # PluginResponse
    SDK_OK,  # SdkStatus
    LT_SEND,  # LinkTypes
    LT_RECV,  # LinkTypes
    LT_BIDI,  # LinkTypes
    TT_MULTICAST,  # TransmissionTypes
    TT_UNICAST,  # TransmissionTypes
    CT_DIRECT,
    CT_INDIRECT,
    ST_STORED_ASYNC,  # SendTypes
    ST_EPHEM_SYNC,  # SendTypes
    CHANNEL_AVAILABLE,
    CHANNEL_UNAVAILABLE,
    ChannelProperties,
    LINK_CREATED,
    LINK_LOADED,
    LINK_DESTROYED,
    StringVector,
)

import sys
sys.path.insert (0, os.path.dirname(__file__))
from Log import *

from AbsWhiteboard import AbsWhiteboard
from DiagPrint import *
from MessageSender import MessageSender
from IOManager import *
from IPSupport import IPSupport
from WhiteboardTransport import WhiteboardTransport
from AbsDestini import AbsDestini
from Pixelfed import Whiteboard
from os import environ


class DestiniPixelfed(AbsDestini):
    def __init__(self, sdk: IRaceSdkComms = None):
        logInfo(f"__init__ called in DestiniPixelfed")
        if 'ANDROID_BOOTLOGO' not in environ:
            os.system ('bash /usr/local/lib/race/comms/DestiniPixelfed/scripts/activate_pixelfed.sh')

        super().__init__(sdk)
        

    def initChannel (self):
        self.channel = "destiniPixelfed"
        if 'ANDROID_BOOTLOGO' not in environ:
            self.pluginPath = "/usr/local/lib/race/comms/DestiniPixelfed"
        else:
            self.pluginPath = "/data/data/com.twosix.race/race/artifacts/comms/DestiniPixelfed/"
            

    def activateChannel(self, handle, channel_gid, role_name) -> int:
        # add protection to check for /ramfs/destiniPixelfed
        #os.system('mkdir -p /ramfs/destiniPixelfed')
        #os.system('tar -xf /usr/local/lib/race/comms/DestiniPixelfed/covers/destini-comms.tar -C /ramfs/Pixlefed')
        #os.system('find /ramfs/destiniPixelfed -type d -exec chmod o+rx {} \;')
        #os.system('find /ramfs/destiniPixelfed -type f -exec chmod o+r {} \;')
        return super().activateChannel(handle, channel_gid, role_name)
        

    def startCheckWBThread (self):
    
        def checkWhiteboardStatus ():
            diagPrint ("In DestiniPixelfed checkWhiteboardStatus*")
            _status = True
            
            while True:
                diagPrint (f"Whiteboard status = {Whiteboard.WB_STATUS}, change time = {Whiteboard.WB_STATUS_CHANGE_TIME}")
                
                if Whiteboard.WB_STATUS != _status and Whiteboard.WB_STATUS_CHANGE_TIME > 0:
                    tdiff = time.time () - Whiteboard.WB_STATUS_CHANGE_TIME
                    diagPrint ("CALLING set_conn_status")
                    _status = Whiteboard.WB_STATUS
    
                    if _status:
                        self.set_conn_status (CONNECTION_OPEN)  
                    elif tdiff > 300:
                        self.set_conn_status (CONNECTION_CLOSED)
                    else:
                        self.set_conn_status (CONNECTION_UNAVAILABLE)
        
                time.sleep (10)

        diagPrint ("In DestiniPixelfed startCheckWBThread*")
        cwb_thread = threading.Thread (target=checkWhiteboardStatus, args=(), daemon=True)
        cwb_thread.start ()


    def startCheckUserModel (self):

        def checkUserModel ():
            diagPrint ("In DestiniPixelfed checkUserModel*")

            # The following requires a single Pixelfed whiteboard

            _wbInstances = self.wbTransport._getMember ('instances')

            if _wbInstances:
                _wbInstance = None
                for _wbInst in _wbInstances.values ():
                    if _wbInst.get ('class') == 'Pixelfed':
                        _wbInstance = _wbInst
                        break

                if _wbInstance is None:
                    diagPrint ("checkUserModel (): unable to find Pixelfed instance")
                    return
            else:
                diagPrint ("checkUserModel (): no whiteboard instances")
                return

            while _wbInstance._userModel:
                with _wbInstance._userModel.condition:
                    _wbInstance._userModel.condition.wait ()

                    if _wbInstance._userModel.isGood:
                        diagPrint ("CALLING set_conn_status")
                        self.set_conn_status (CONNECTION_OPEN)

                    else:
                        diagPrint ("CALLING set_conn_status")
                        self.set_conn_status (CONNECTION_UNAVAILABLE)
                        break

        diagPrint ("In DestiniPixelfed startCheckUserModel*")
        ckum_thread = threading.Thread (target=checkUserModel, args=(), daemon=True)
        ckum_thread.start ()

    
    def channelSendPackage (self, handle, conn, data):
        """
            Sends the provided raw data over the specified direct link connection
 
        Args:
            handle: The RaceHandle to use for updating package status in
                    onPackageStatusChanged
            conn: The connection to use to send the package
            data: The raw data to send

        Returns:
            None
        """

        diagPrint ("Destini Pixelfed: Entering channelSendPackage")
        
        m = hashlib.new ('md5')
        m.update (data)
        diagPrint (f"Destini Pixelfed: in channelSendPackage {m.hexdigest ()} {len (data)} {conn.host}")
        datalen = len (data)
        link_profile = self.link_profiles.get(conn.link_id)
        _msgSender = MessageSender.messageSender (conn.host, self.wbTransport, maxQueuedBytes = 2950, whiteboards = link_profile.get('whiteboards'))
        _transport = 'whiteboard'
        
        
        rval = _msgSender.sendMessage (data, IOM_CT_GENERAL, self.wbTransport)
        diagPrint ("returning from _msgSender.sendMessage", diagPrint)
        
        if rval < 0:
            diagPrint (f"_msgSender.sendMessage failed: {rval}")
            self.race_sdk.onPackageStatusChanged(
                handle, PACKAGE_FAILED_GENERIC, RACE_BLOCKING
            )
            return


        diagPrint (f"Destini Pixelfed: data sent over {_transport}", diagPrint)

        self.race_sdk.onPackageStatusChanged (
            handle, PACKAGE_SENT, RACE_BLOCKING
        )




