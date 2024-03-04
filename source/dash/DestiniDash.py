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
    CT_DIRECT,  # TransmissionTypes
    CT_INDIRECT,  # TransmissionTypes
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
from PixelfedSelenium import Whiteboard


class DestiniDash (AbsDestini):

    def __init__(self, sdk: IRaceSdkComms = None):
        logInfo(f"__init__ called in DestiniDash")
        os.system ('bash /usr/local/lib/race/comms/DestiniDash/scripts/activate_dash.sh init')
        super().__init__(sdk)


    def initChannel (self):
        self.channel = "destiniDash"
        self.pluginPath = "/usr/local/lib/race/comms/DestiniDash"

        
    def activateChannel(self, handle, channel_gid, role_name) -> int:
        # Generalize this script to have an extra parameter to start up to start up webserver
        logInfo("In activateChannel " + channel_gid)
        os.system ('bash /usr/local/lib/race/comms/DestiniDash/scripts/activate_dash.sh activate')
        return super().activateChannel(handle, channel_gid, role_name)




    def startCheckWBThread (self):
        diagPrint ("In DestiniDash startCheckWBThread*")
        cwb_thread = threading.Thread (target=self.checkWhiteboardStatus, args=(), daemon=True)
        cwb_thread.start ()

    def startCheckUserModel (self):

        def checkUserModel ():
            diagPrint ("In DestiniDash checkUserModel*")
    
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

        diagPrint ("In DestiniDash startCheckUserModel*")
        ckum_thread = threading.Thread (target=checkUserModel, args=(), daemon=True)
        ckum_thread.start ()



    def checkWhiteboardStatus (self):
        diagPrint ("In DestiniDash checkWhiteboardStatus*")
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
        

    def getConnType (self):
        diagPrint (f"setting conn type to CT_DIRECT")
        return CT_DIRECT



    def extendWhiteboards (self):
        if self.isServer:
            self.wbTransport.addInstance(self.active_persona, {'class': 'DashSvr'})

    def linkReceiveFilter (self):
        return lambda _h: not _h.startswith ('race-server-') or _h == self.active_persona

    def linkTransmitFilter (self, persona):
        if persona.startswith("race-server"):
            self.wbTransport.addInstance(persona, {'class': 'DashSvr'})
            _filter = self.linkReceiveFilter()
        else:
            _filter = None
            
        return _filter
        
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

        diagPrint ("DestiniDash channelSendPackage: called")

        m = hashlib.new ('md5')
        m.update (data)
        diagPrint (f"in channelSendPackage {m.hexdigest ()} {len (data)}")
        diagPrint (f"in channelSendPackage persona={self.active_persona} conn.host = {conn.host}")

        _msgSender = MessageSender.messageSender (conn.host, self.wbTransport, maxQueuedBytes = 16100000)
        svr2svr = '-server-' in self.active_persona and '-server-' in conn.host

        try:
            if svr2svr:
                _transport = 'Dash'
                # DASH message must be processed through _recv_message as type IOM_MT_GENERAL
                rval = _msgSender.sendMessage (data, IOM_CT_D_SVR, self.wbTransport, IOM_MT_GENERAL)
            else:
                _transport = 'Pixelfed'
                rval = _msgSender.sendMessage (data, IOM_CT_GENERAL, self.wbTransport)
            
            diagPrint ("returning from _msgSender.sendMessage")
        except Exception as e:
            diagPrint(f"_msgSender.sendMessage failed transport = {_transport} {e}")
            rval = -99
            
        if rval < 0:
            diagPrint (f"_msgSender.sendMessage failed: {rval}")
            self.race_sdk.onPackageStatusChanged(
                handle, PACKAGE_FAILED_GENERIC, RACE_BLOCKING
            )
            return

        diagPrint (f"DestiniDash channelSendPackage: data sent over {_transport}")

        self.race_sdk.onPackageStatusChanged (
            handle, PACKAGE_SENT, RACE_BLOCKING
        )



