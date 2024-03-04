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

from AbsWhiteboard import AbsWhiteboard
from DiagPrint import *
from MessageSender import MessageSender
from IOManager import *
from IPSupport import IPSupport
from WhiteboardTransport import WhiteboardTransport
from AbsDestini import AbsDestini
from Avideo import Whiteboard




class DestiniAvideo (AbsDestini):

    def __init__(self, sdk: IRaceSdkComms = None):
        logInfo(f"__init__ called in DestiniAvideo")
        os.system ('bash /usr/local/lib/race/comms/DestiniAvideo/scripts/activate_avideo.sh')
        super().__init__(sdk)


    def initChannel (self):
        self.channel = "destiniAvideo"
        self.pluginPath = "/usr/local/lib/race/comms/DestiniAvideo"

    def activateChannel(self, handle, channel_gid, role_name) -> int:        
        return super().activateChannel(handle, channel_gid, role_name)


    def startCheckWBThread (self):
        diagPrint ("In DestiniAvideo startCheckWBThread*")
        cwb_thread = threading.Thread (target=self.checkWhiteboardStatus, args=(), daemon=True)
        cwb_thread.start ()

    def startCheckUserModel (self):

        def checkUserModel ():
            diagPrint ("In DestiniAvideo checkUserModel*")
    
            while self._userModel:
                with self._userModel.condition:
                    self._userModel.condition.wait ()
    
                    if self._userModel.isGood:
                        diagPrint ("CALLING set_conn_status")
                        self.set_conn_status (CONNECTION_OPEN)
    
                    else:
                        diagPrint ("CALLING set_conn_status")
                        self.set_conn_status (CONNECTION_UNAVAILABLE)
                        break

        diagPrint ("In DestiniAvideo startCheckUserModel*")
        ckum_thread = threading.Thread (target=checkUserModel, args=(), daemon=True)
        ckum_thread.start ()



    def checkWhiteboardStatus (self):
        diagPrint ("In DestiniAvideo checkWhiteboardStatus*")
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
                    self.set_conn_status(CONNECTION_UNAVAILABLE)
    
            time.sleep (10)



    def channelSendPackage(self, handle, conn, data):
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

        diagPrint ("DestiniAvideo channelSendPackage called")

        m = hashlib.new ('md5')
        m.update (data)
        diagPrint (f"in channelSendPackage {m.hexdigest ()} {len (data)} {conn.host}")

        datalen = len (data)
        _msgSender = MessageSender.messageSender (conn.host, self.wbTransport, maxQueuedBytes = 8000000)

        _transport = 'avideo'
         
        rval = _msgSender.sendMessage (data, IOM_CT_AVIDEO, self.wbTransport)
        diagPrint ("returning from _msgSender.sendMessage", logDebug)
        
        if rval < 0:
            diagPrint (f"_msgSender.sendMessage failed: {rval}", logError)
            self.race_sdk.onPackageStatusChanged(
                handle, PACKAGE_FAILED_GENERIC, RACE_BLOCKING
            )
            return


        diagPrint (f"DestiniAvideo: data sent over {_transport}", logDebug)

        self.race_sdk.onPackageStatusChanged (
            handle, PACKAGE_SENT, RACE_BLOCKING
        )



