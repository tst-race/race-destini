"""
"""
# /usr/bin/env/python3

import inspect
import json
import os
import time
import hashlib
from typing import Any, Dict, Optional

# RACE Libraries
from response_logger import *
from channels import *

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
    CONNECTION_UNAVAILABLE,
    CHANNEL_FAILED,
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
from Log import *

from DiagPrint import *
from IOManager import *
from IPSupport import IPSupport
from WhiteboardTransport import WhiteboardTransport


PluginResponse = int  # mypy type alias



class AbsDestini (IRacePluginComms):

    """

    Attributes:
        connections (dict): dict of CommsConn objects, keyed by connection_id string
        link_profiles (dict): dict of string-form link profiles, keyed by link_id string
        sdk (RaceSdk): the sdk object
    """

    response_logger  = ResponseLogger()
    channel = ""
    RecvDupMsgLock   = threading.RLock ()
    RecvMsgHashes    = []
    MaxRecvMsgHashes = 10000

    IndirectChannels = ("destiniPixelfed", "destiniAvideo")
    DirectChannels   = ("destiniDash")

    class CommsConn:

        """

        Attributes:
            connection_ids (list of str): identifiers for connection, to allow referencing conn
                                          without passing around the object. one connection ha many
                                          conn ids.
            host (str): hostname to use with sockets
            port (str): port to use with sockets
            link_id (str): unique identifier for link used by this connection
            link_type (enum): does this conn send? receive? - LT_SEND / LT_RECV / LT_BIDI
            sock (socket.socket): socket object used by connection
            thread (threading.Thread): thread on which socket is being monitored
        """


        def __init__(self, connection_id: str):
            """
                Initialize connection object with valid unique connection_id

            Args:
                connection_id: The initial/only connection ID
            """

            # Connection Tracking
            self.connection_ids = [connection_id]

            # Link Metadata
            self.link_id = None
            self.link_type = None

            # Monitoring Values
            self.terminate = False
            self.thread = None
            self.sock = None

            # Link Profile Attributes
            self.host = None
            self.port = None
            self.multicast = False
            self.frequency = None
            self.hashtag = None
            self.status = CONNECTION_OPEN



    def __init__(self, sdk: IRaceSdkComms = None):
        """
        Purpose:
            Initialize the plugin
        Args:
            sdk: SDK object

        """

        try:
            logInfo(f"AbsDestini: __init__ called")
            self.__init_safe(sdk)
        except Exception as err:
            logError(f"Plugin failed to __initialize__: {err}")
            return PLUGIN_OK


    def __init_safe(self, sdk: IRaceSdkComms = None):

        super().__init__()

        if sdk is None:
            raise Exception("sdk was not passed to plugin")

        self.race_sdk = sdk

        # set channel name do any channel specific initializations here
        self.initChannel()
        self.connections = {}
        self.connections_lock = threading.RLock()
        self.link_profiles = {}
        self.link_properties = {}
        self.lt_str_map = {
            "send": LT_SEND,
            "receive": LT_RECV,
            "recv": LT_RECV,
            "bidirectional": LT_BIDI,
            "bidi": LT_BIDI,
        }

        self.active_persona = None

        # Current statuses of the available channels. Used to prevent Network Manager performing
        # operations on channels that aren't (yet) active.
        self.channel_status = {
            self.channel: CHANNEL_UNAVAILABLE,
        }


        # Map of channel GIDs keys to a set of link IDs active in that channel.
        self.links_in_channels = {
            self.channel: set(),
        }

        # Map of user input handles (int) to member/attribute names

        self._inputMembers = dict ()

        self._hostname = "no-hostname-provided-by-user"
        self._runmode  = "run mode not provided"
        self._request_start_port_handle = None
        self._request_hostname_handle = None
        self._request_runmode_handle = None
        self.thread = threading.Thread(target=self._keep_alive, args=())
        self.thread.start()
        self.user_input_requests = set()

        self.wbTransport = None

    def __del__(self):
        """
        Purpose:
            Destructure for the plugin object.
            Shuts down the plugin to ensure a clean shutdown of all connections.
        """

        self.shutdown()


    @staticmethod
    def _send_message (to_ip, wbTransport, out_data, cType):

        rval = -1

        try:
            ip_str = IPSupport.IP_string (to_ip)
            rval   = wbTransport.sendMsg (ip_str, out_data, cType)

            m = hashlib.new ('md5')
            m.update (out_data)
            diagPrint (f"In _send_message.... to_ip={ip_str} {m.hexdigest ()} {len (out_data)}")

            if not rval:
                diagPrint (f"send failed in _send_message: {rval}", logError)
        except Exception as e:
            diagPrint(f'AbsDestini: uncaught exception in _send_message {e}')

        return rval

    @classmethod
    def _recv_message(cls, _fromIP, refconst, in_data):
        diagPrint (f"_recv_mesg fromIP={IPSupport.IP_string (_fromIP)} {len (in_data)}")
        m = hashlib.new ('md5')
        m.update (in_data)
        msgDigest = m.hexdigest ()
        diagPrint (f"in _recv_message {msgDigest} {len (in_data)}")
        with cls.RecvDupMsgLock:
            if len (cls.RecvMsgHashes) >= cls.MaxRecvMsgHashes:
                cls.RecvMsgHashes.pop (0)
            if msgDigest in cls.RecvMsgHashes:
                diagPrint(f'WARNING: AbsDestini: _recv_message: ignoring duplicate message from {IPSupport.IP_string (_fromIP)} {msgDigest} {len (in_data)}')
                return
            else:
                cls.RecvMsgHashes.append (msgDigest)
        try:
            enc_pkg = EncPkg (in_data)
            response = refconst[0].race_sdk.receiveEncPkg (enc_pkg, refconst[0].get_conn_ids(), RACE_BLOCKING)
            if response.status != SDK_OK:
                diagPrint(f"SDK failed with status {response.status}")
        except Exception as e:
            diagPrint(f'AbsDestini: _recv_message: Uncaught Exception on call to receiveEncPkg {e}')


    ###################
    #                 #
    # Virtual methods #
    #                 #
    ###################


    # set the channel name and any other channel specific initialization
    def initChannel (self):
        # https://stackoverflow.com/questions/33162319/how-can-get-current-function-name-inside-that-function-in-python
        raise NotImplementedError ('{}.{} () not implemented'.format (self._className (),
                                                                      inspect.getframeinfo (inspect.currentframe ()).function))


    def isDirectChannel (self):
        return self.channel in self.DirectChannels

    def extendWhiteboards (self):
        pass

    def linkReceiveFilter (self):
        #return None
        return lambda _h: _h != self.active_persona

    def linkTransmitFilter (self, _persona):
        return not self.linkReceiveFilter ()
        #return lambda _h: _h == self.active_persona

    def getConnType (self):
        diagPrint (f"setting conn type to CT_INDIRECT")
        return CT_INDIRECT

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
        raise NotImplementedError ('{}.{} () not implemented'.format (self._className (),
                                                                      inspect.getframeinfo (inspect.currentframe ()).function))




    def init (self, plugin_config: PluginConfig) -> int:
        """
        Purpose:
            Initializing the application. This is called before both plugins are
            initalized so we cannot make calls to the other plugin functionality
        Args:
            plugin_config (PluginConfig): Config object containing dynamic config variables (e.g. paths)
        Returns:
            PluginResponse: The status of the plugin in response to this call
        """

        try:
            return self.init_safe(plugin_config)
        except Exception as err:
            logError(f"Plugin failed to initialize: {err}")
            return PLUGIN_OK



    def init_safe(self, plugin_config: PluginConfig):
        """
        Purpose:
            Initializing the application. This is called before both plugins are
            initalized so we cannot make calls to the other plugin functionality
        Args:
            plugin_config (PluginConfig): Config object containing dynamic config variables (e.g. paths)
        Returns:
            PluginResponse: The status of the plugin in response to this call
        """

        logInfo("init called")
        logInfo(f"loggingDirectory: {plugin_config.loggingDirectory}")
        logInfo(f"auxDataDirectory: {plugin_config.auxDataDirectory}")
        logInfo(f"tmpDirectory: {plugin_config.tmpDirectory}")



        self.active_persona = self.race_sdk.getActivePersona()
        logDebug(f"init: I am {self.active_persona}")

        self.link_profiles = {}
        self.link_properties = {}
        self.link_profile_config = {}

        logInfo(f"init stage 1")

        IOManager.SetHostIP (IPSupport.Persona_IP_string(self.active_persona))
        for cType in (IOM_CT_ORDERED, IOM_CT_GENERAL, IOM_CT_AVIDEO, IOM_CT_D_SVR):
            IOManager.SetSendMsg (self._send_message, cType)

        # DashSvr.py:Whiteboard calls IOManager.SetProcessMsg (_recvRendezvousMsg, IOM_MT_D_SVR)
        for mType in (IOM_MT_GENERAL, IOM_MT_AVIDEO):
            IOManager.SetProcessMsg (self._recv_message, mType)


        IOManager.SetProcessMsg (self._recv_message, IOM_MT_GENERAL)

        logInfo(f"init stage 2")

        refcon      = (self, self.get_conn_ids())
        logInfo(f"init stage 3")

        processMsgs = {IOM_CT_GENERAL: lambda _msg, _: IOManager.Examine (_msg, IOM_CT_GENERAL, 0, refcon),
                       IOM_CT_AVIDEO:  lambda _msg, _: IOManager.Examine (_msg, IOM_CT_AVIDEO, 0, refcon),
                       IOM_CT_D_SVR:   lambda _msg, _: IOManager.Examine (_msg, IOM_CT_D_SVR,   0, refcon)}

        self.wbTransport = WhiteboardTransport (self.active_persona, processMsgs)
        self.createTransports = True

        jsonfile = "whiteboard.stealth.json" if (self._runmode == "stealth") else "whiteboard.json"

        if self.wbTransport.processWhiteboardSpec (os.path.join (self.pluginPath, jsonfile)):
            self.wbTransport.createTransports ()
            self.createTransports = False

        self.isServer = self.active_persona.startswith("race-server-")

        self.extendWhiteboards()

        for brdcastHost, brdcastSeed in self.wbTransport.broadcastHosts.items ():
            IOManager.SetBroadcastHost (brdcastHost, brdcastSeed)

        self.race_sdk.writeFile(
            "initialized.txt", "Comms Python Plugin Initialized\n".encode("utf-8")
        )

        tmp = bytes(self.race_sdk.readFile("initialized.txt")).decode("utf-8")
        logDebug("Type of readFile return: {}".format(type(tmp)))
        logDebug(f"Read Initialization File: {tmp}")

        # The following assumes a single whiteboard

        logInfo("starting checkwhiteboard status thread")
        self.startCheckWBThread ()

        logInfo("starting checkusermodel status thread")
        self.startCheckUserModel ()

        logInfo("init returned")
        return PLUGIN_OK


    def startCheckWBThread (self):
        # overloaded by Pixelfed plugin for now...
        pass

    def startCheckUserModel (self):
        # overloaded by Pixelfed plugin for now...
        pass

    def get_conn_ids (self):
        conn_id_list = []
        diagPrint("In get_conn_ids")
        with self.connections_lock:
            for c in self.connections.values():
                conn_id_list.extend(c.connection_ids)
                diagPrint(f"adding conn ids {conn_id_list}")
        return conn_id_list


    def set_conn_status (self, status):
        diagPrint("In set_conn_status")

        with self.connections_lock:
            for conn in self.connections.values():
                for conn_id in conn.connection_ids:
                    if conn.status == status:
                        continue

                    self.race_sdk.onConnectionStatusChanged(
                        NULL_RACE_HANDLE,
                        conn_id,
                        status,
                        self.link_properties[conn.link_id],
                        RACE_BLOCKING,
                    )

                    conn.status = status

                    if status == CONNECTION_CLOSED:
                        conn.connection_ids.remove (conn_id)


    def onUserAcknowledgementReceived(self, _handle) -> int:
        return PLUGIN_OK


    def registerUserInput (self, handle_str: str, memberName: str, plugin_specific: bool):
        if plugin_specific:
            _input = self.race_sdk.requestPluginUserInput (handle_str, "Enter " + handle_str + ":", True)
        else:
            _input = self.race_sdk.requestCommonUserInput (handle_str)

        if _input.status == SDK_OK:
            self.user_input_requests.add (_input.handle)
            self._inputMembers[_input.handle] = memberName
            self.user_input_requests.add (_input.handle)
        else:
            logWarning ("Failed to request " + handle_str + " from user")


    def requestUserInput(self, _handle, _channel_gid, _role_name) -> int:
        # Activate a specific channel

        self.registerUserInput ("runmode",  "_runmode", True)
        self.registerUserInput ("hostname", "_hostname", False)

        return PLUGIN_OK


    def _makeChannelAvailable(self):
        self.channel_status[self.channel] = CHANNEL_AVAILABLE
        self.race_sdk.onChannelStatusChanged(
            NULL_RACE_HANDLE,
            self.channel,
            CHANNEL_AVAILABLE,
            get_default_channel_properties_for_channel(self.race_sdk, self.channel),
            RACE_BLOCKING,
        )
        diagPrint(f"making channel available {self.channel}")


    def activateChannel(self, _handle, channel_gid, _role_name) -> int:
        return self.requestUserInput (_handle, channel_gid, _role_name)


    def shutdown(self) -> int:
        """
        Purpose:
            Iterate through all of the existing connections, close each.
        Returns:
            PluginResponse: The status of the plugin in response to this call
        """

        logInfo("shutdown called")
        try:
            self.wbTransport.shutdown()

            with self.connections_lock:
                for conn_id in self.connections.keys():
                    self.closeConnection(NULL_RACE_HANDLE, conn_id)
        except:
            pass

        return PLUGIN_OK



    def parsePropertySet(self, prop_json: Dict[str, Any]) -> LinkPropertySet:
        """
        Purpose:
            Parse the link property set from the given generic dict of values
        Args:
            prop_json: dict of link property values
        Returns:
            LinkPropertySet object
        """
        propset = LinkPropertySet()
        if prop_json is not None:
            propset.bandwidth_bps = prop_json.get("bandwidth_bps", -1)
            propset.latency_ms = prop_json.get("latency_ms", -1)
            propset.loss = prop_json.get("loss", -1.0)

        return propset

    def parsePropertyPair(self, prop_json: Dict[str, Any]) -> LinkPropertyPair:
        """
        Purpose:
            Parse the send/receive link property pair from the given
            generic dict of values
        Args:
            prop_json: dict of link property pair values
        Returns:
            LinkPropertyPair object
        """
        pair = LinkPropertyPair()
        if prop_json is not None:
            pair.send = self.parsePropertySet(prop_json.get("send", None))
            pair.receive = self.parsePropertySet(prop_json.get("receive", None))

        return pair



    def sendPackage(self, handle: int, conn_id: str, enc_pkg: EncPkg, timeoutTimestamp: float, batchId: int) -> int:
        try:
            return self.sendPackage_safe(handle, conn_id, enc_pkg, timeoutTimestamp, batchId)
        except Exception as err:
            logError(f"PluginCommsTwoSixPython: sendPackage failed: {err}")
            return None

    def sendPackage_safe(self, handle: int, conn_id: str, enc_pkg: EncPkg, _timeoutTimestamp: float, _batchId: int) -> int:
        """
        Purpose:
           Sends the provided EncPkg object on the connection identified by conn_id
            handle: The RaceHandle to use for updating package status in
                    onPackageStatusChanged
            conn_id: The ID of the connection to use to send the package
            enc_pkg: The encrypted package to send

        Returns:
            PluginResponse: The status of the plugin in response to this call
        """

        diagPrint ("sendPackage called")

        with self.connections_lock:
            conn = self.connections[conn_id]

        # Fail if this is a receive-only connection
        if conn.link_type == LT_RECV:
            logDebug("Attempting to send on a receive-only connection")
            return PLUGIN_ERROR

        connect_type_string = "multicast" if conn.multicast else "direct"
        logInfo(f"sendPackage: sending over {connect_type_string} link")

        data = bytes(enc_pkg.getRawData())

        self.channelSendPackage(handle, conn, data)

        diagPrint ("sendPackage returned")
        return PLUGIN_OK




    def openConnection(
        self,
        handle: int,
        link_type: int,
        link_id: str,
        link_hints: Optional[str] = None,
        send_timeout: int = RACE_UNLIMITED,
    ) -> int:
        try:
            return self.openConnection_safe(handle, link_type, link_id, link_hints, send_timeout)
        except Exception as err:
            logError(f"PluginCommsTwoSixPython: openConnection failed: {err}")
            return None


    def openConnection_safe(self, handle, link_type, link_id, link_hints, _send_timeout):
        """

        Args:
            handle: The RaceHandle to use for onConnectionStatusChanged calls
            link_type (enum): LT_SEND / LT_RECV / LT_BIDI
            link_id (str): The ID of the link that the connection should be opened on
            link_hints: Additional optional configuration information
                provided by Network Manager as a stringified JSON object

        Returns:
                    PluginResponse: The status of the plugin in response to this call
        """
        logInfo("openConnection called")
        logDebug(f"    cached link profile: {self.link_profiles[link_id]}")
        logDebug(f"    link_hints: {link_hints}")


        if not self.link_profiles.get(link_id):
            logError(f"openConnection: no link profile found for link ID {link_id}")
            return PLUGIN_ERROR

        if link_type == LT_RECV:
            self.wbTransport.startReceiveLink (link_id)

        with self.connections_lock:
            for c in self.connections.values():
                if c.link_id == link_id:
                    logInfo("connection already exists.")
                    connection_id = self.race_sdk.generateConnectionId(link_id)
                    self.connections[connection_id] = c
                    c.connection_ids.append(connection_id)
                    c.status = CONNECTION_OPEN
                    self.race_sdk.onConnectionStatusChanged(
                            handle,
                            connection_id,
                            CONNECTION_OPEN,
                            self.link_properties[link_id],
                            RACE_BLOCKING,
                        )
                    return PLUGIN_OK

        connection_id = self.race_sdk.generateConnectionId(link_id)
        conn = self.CommsConn(connection_id)
        with self.connections_lock:
            self.connections[connection_id] = conn

        conn.link_id = link_id
        conn.link_type = link_type

        link_profile = self.link_profiles[link_id]

        # Parse Link Profile
        conn.port = link_profile.get("port", None)

        if link_profile.get("group", None):
            conn.host = link_profile.get("group", None)
            conn.multicast = True
        else:
            conn.host = link_profile.get("persona", "localhost")
            conn.multicast = False

        conn.frequency = link_profile.get("frequency", 0)
        conn.hashtag = link_profile.get("hashtag", "")

        self.race_sdk.onConnectionStatusChanged (
            handle,
            connection_id,
            CONNECTION_OPEN,
            self.link_properties[link_id],
            RACE_BLOCKING,
        )

        return PLUGIN_OK


    def closeConnection(self, handle, conn_id):
        try:
            return self.closeConnection_safe(handle, conn_id)
        except Exception as err:
            logError(f"PluginCommsTwoSixPython: closeConnection failed: {err}")
            return None



    def closeConnection_safe(self, handle, conn_id):
        """Closes the socket being used by a connection, stops the thread, deletes the CommsConn
        object.

        Args:
            conn_id (int): the unique identifier string for the connection to be closed
        """
        logInfo("closeConnection called")
        logDebug(f"    connection: {conn_id}")

        with self.connections_lock:
            if not conn_id in self.connections:
                logWarning(f"No connection found: {conn_id}")
                return PLUGIN_ERROR

            # Unlink the connection from the given connection ID--the connection may
            # still be in use with another connection ID
            conn = self.connections.pop(conn_id)
            conn.connection_ids.remove(conn_id)

            # If this was the last logical connection, shut down the actual link
            if len(conn.connection_ids) == 0:
                try:
                    conn.terminate = True
                    if conn.sock:
                        conn.sock.close()
                    # the monitor thread will die off eventually
                except Exception as err:
                    logError(f"Closing connection err: {err}")
                    return PLUGIN_ERROR

            self.race_sdk.onConnectionStatusChanged(
                handle,
                conn_id,
                CONNECTION_CLOSED,
                self.link_properties[conn.link_id],
                RACE_BLOCKING,
            )
            return PLUGIN_OK
        # end of with self.connections_lock


    def destroyLink(self, handle, link_id):
        logPrefix = f"destroyLink: (handle: {handle}, link ID: {link_id}): "
        logDebug(f"{logPrefix}called")

        channel_gid_for_link = None
        for channel_gid, link_ids_in_channel in self.links_in_channels.items():
            if link_id in link_ids_in_channel:
                channel_gid_for_link = channel_gid
                break
        if not channel_gid:
            logError(f"{logPrefix}failed to find link ID: {link_id}")
            return PLUGIN_ERROR

        # Notify the SDK that the link has been destroyed
        link_props = get_default_link_properties_for_channel(
            self.race_sdk, channel_gid_for_link
        )


        self.race_sdk.onLinkStatusChanged(
            handle,
            link_id,
            LINK_DESTROYED,
            link_props,
            RACE_BLOCKING,
        )

        # Close all the connections in the given link.
        with self.connections_lock:
            for conn_id, conn in self.connections.items():
                if conn.link_id == link_id:
                    self.closeConnection(handle, conn_id)

        # Remove the link ID reference.
        self.links_in_channels[channel_gid_for_link].remove(link_id)

        logDebug(f"{logPrefix}returned")
        return PLUGIN_OK

    def createLink(self, handle, channel_gid):
        log_prefix = f"createLink: (handle: {handle}, channel GID: {channel_gid}): "
        diagPrint(f"{log_prefix}called")

        if self.channel_status.get(channel_gid) != CHANNEL_AVAILABLE:
            logError(f"{log_prefix}channel not available.")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        link_id = self.race_sdk.generateLinkId(channel_gid)
        if not link_id:
            diagPrint(f"{log_prefix}sdk failed to generate link ID")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        if channel_gid == self.channel:
            diagPrint (f"{log_prefix}creating indirect link with ID: {link_id}")

            if self.createTransports:
                self.wbTransport.createTransports ()
                self.createTransports = False

            link_profile = self.wbTransport.receiveLink (link_id, self.linkReceiveFilter())
            self.link_profiles[link_id] = link_profile

            link_props = get_default_link_properties_for_channel(self.race_sdk, channel_gid)
            link_props.linkType = LT_RECV
            link_props.linkAddress = json.dumps (link_profile)
            self.link_properties[link_id] = link_props

            self.links_in_channels[channel_gid].add(link_id)
            self.race_sdk.onLinkStatusChanged(
                handle, link_id, LINK_CREATED, link_props, RACE_BLOCKING
            )
            self.race_sdk.updateLinkProperties(link_id, link_props, RACE_BLOCKING)
        else:
            logError(f"{log_prefix}invalid channel GID")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        logDebug(
            f"{log_prefix}created link with ID: {link_id} and address: {link_props.linkAddress}"
        )
        logDebug(f"{log_prefix}returned")
        return PLUGIN_OK


    def createLinkFromAddress(self, handle, channel_gid, link_address):
        log_prefix = (
            f"createLinkFromAddress: (handle: {handle}, channel GID: {channel_gid}): "
        )
        logDebug(f"{log_prefix}called")

        if self.channel_status.get(channel_gid) != CHANNEL_AVAILABLE:
            logError(f"{log_prefix}channel not available.")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        link_id = self.race_sdk.generateLinkId(channel_gid)
        link_props = get_default_link_properties_for_channel(self.race_sdk, channel_gid)

        if not link_id:
            logDebug(f"{log_prefix}sdk failed to generate link ID")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        if channel_gid == self.channel:
            diagPrint (f"{log_prefix}creating indirect link with ID: {link_id}")

            link_props.linkType = LT_RECV
            link_props.linkAddress = link_address

            link_profile = json.loads(link_address)
            self.link_profiles[link_id]  = link_profile
            self.link_properties[link_id] = link_props

            if self.createTransports:
                self.wbTransport.createTransports ()
                self.createTransports = False

            # given than genesis links occur before dynamic links set the WhiteboardTransport tagSeed accordingly
            if link_profile['tag_seed'].startswith (self.active_persona):
                self.wbTransport.tagSeed = link_profile['tag_seed']

            # must deal with multicast tag seeds

            self.wbTransport.receiveLinkFromAddress (link_id, link_profile['persona'], link_profile['tag_seed'], self.linkReceiveFilter())

            self.links_in_channels[channel_gid].add(link_id)
            self.race_sdk.onLinkStatusChanged(
                handle, link_id, LINK_CREATED, link_props, RACE_BLOCKING
            )
            self.race_sdk.updateLinkProperties(link_id, link_props, RACE_BLOCKING)
        else:
            logError(f"{log_prefix}invalid channel GID")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        logDebug(f"{log_prefix}returned")
        return PLUGIN_OK



    def loadLinkAddress(self, handle, channel_gid, link_address):
        log_prefix = f"loadLinkAddress: (handle: {handle}, channel GID: {channel_gid}): "
        diagPrint(f"{log_prefix}called")

        if self.channel_status.get(channel_gid) != CHANNEL_AVAILABLE:
            logError(f"{log_prefix}channel not available.")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        link_id = self.race_sdk.generateLinkId(channel_gid)
        if not link_id:
            diagPrint(f"{log_prefix}sdk failed to generate link ID")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        if channel_gid == self.channel:
            diagPrint(f"{log_prefix}loading indirect link with ID: {link_id}")
            link_props = get_default_link_properties_for_channel(
                self.race_sdk, channel_gid
            )

            link_props.linkType = LT_SEND
            link_profile = json.loads(link_address)
            self.link_profiles[link_id] = link_profile
            link_profile['persona'] = link_profile['s_persona']
            persona = link_profile['persona']

            diagPrint(f"HELLO: Loading link_address for persona {persona}.  link_id: {link_id} link_profile: {link_profile}")
            self.link_properties[link_id] = link_props
            self.wbTransport.transmitLink (link_profile, self.linkTransmitFilter(persona))
            self.links_in_channels[channel_gid].add(link_id)
            self.race_sdk.onLinkStatusChanged(
                handle, link_id, LINK_LOADED, link_props, RACE_BLOCKING
            )
            self.race_sdk.updateLinkProperties(link_id, link_props, RACE_BLOCKING)
        else:
            logError(f"{log_prefix}invalid channel GID")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        logDebug(f"{log_prefix}returned")
        return PLUGIN_OK


    # IGNORE FOR NOW... SEEMS INCOMPLETE
    def loadLinkAddresses(self, handle, channel_gid, _link_addresses):
        log_prefix = (
            f"loadLinkAddresses: (handle: {handle}, channel GID: {channel_gid}): "
        )
        logDebug(f"{log_prefix}called")

        if self.channel_status.get(channel_gid) != CHANNEL_AVAILABLE:
            logError(f"{log_prefix}channel not available.")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        if get_default_channel_properties_for_channel(
                self.race_sdk, channel_gid
        ).multiAddressable:
            logError(log_prefix + "API not supported for this channel")
            self.race_sdk.onLinkStatusChanged(
                handle,
                "",
                LINK_DESTROYED,
                LinkProperties(),
                RACE_BLOCKING,
            )
            return PLUGIN_ERROR

        logDebug(f"{log_prefix}returned")
        return PLUGIN_OK

    def deactivateChannel(self, handle, channel_gid):
        log_prefix = (
            f"deactivateChannel: (handle: {handle}, channel GID: {channel_gid}): "
        )
        logDebug(f"{log_prefix}called")

        if self.channel_status.get(channel_gid):
            logError(f"{log_prefix}channel not available.")
            return PLUGIN_ERROR

        self.channel_status[channel_gid] = CHANNEL_UNAVAILABLE

        self.race_sdk.onChannelStatusChanged(
            NULL_RACE_HANDLE,
            channel_gid,
            CHANNEL_UNAVAILABLE,
            get_default_channel_properties_for_channel(self.race_sdk, channel_gid),
            RACE_BLOCKING,
        )

        # Destroy all links in channel, and implicitly all the connections in each link.
        for link_id in self.links_in_channels[channel_gid]:
            self.destroyLink(handle, link_id)

        # Remove all links IDs associated with the channel
        self.links_in_channels[channel_gid].clear()

        logDebug(f"{log_prefix}returned")
        return PLUGIN_OK

    """
    Purpose:
        Notify Comms about received user input response
    Args:
        handle: The handle for this callback
        answered: True if the response contains an actual answer to the input prompt, otherwise
            the response is an empty string and not valid
        response: The user response answer to the input prompt
    Returns:
        PluginResponse: The status of the Plugin in response to this call
    """
    def onUserInputReceived(
        self,
        handle: int,
        _answered: bool,
        response: str,
    ) -> PluginResponse:
        log_prefix = f"onUserInputReceived: (handle: {handle} {self.user_input_requests}): "
        logDebug(f"{log_prefix}called")

        # Note: if handle == 1 and its associated memberName is '_foo',
        # the following line is equivalent to
        #    self._foo = response
        #
        setattr (self, self._inputMembers.get (handle), response)
        self.user_input_requests.discard(handle)

        if not self.user_input_requests:
            self._makeChannelAvailable ()

        logDebug(f"{log_prefix}returned")
        return PLUGIN_OK

    def flushChannel(
        self, _handle: int, _channelGid: str, _batchId: int
    ) -> PluginResponse:
        logDebug(f"flushChannel: plugin does not support flushing")
        return PLUGIN_ERROR


    def _keep_alive(self):
        logDebug(
            "Started keep alive thread: Need to determine best method to keep Python threads "
            "running..."
        )
        while True:
            time.sleep(60)

