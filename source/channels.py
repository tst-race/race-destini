"""
    Purpose:
        Module for maintaining RACECOMMS channel properties.
"""

from commsPluginBindings import (
    IRaceSdkComms,
    LinkProperties,
    LinkPropertySet,
    ChannelProperties,
    LD_LOADER_TO_CREATOR,
    TT_UNICAST,
    CT_DIRECT,
    ST_EPHEM_SYNC,
    LD_BIDI,
    TT_MULTICAST,
    CT_INDIRECT,
    ST_STORED_ASYNC,
    LT_BIDI,
)


_INT_MAX = 2147483647


def get_default_channel_properties_for_channel(
    sdk: IRaceSdkComms, channel_gid: str
) -> ChannelProperties:
    return sdk.getChannelProperties(channel_gid)



def get_default_link_properties_for_channel(
        sdk: IRaceSdkComms, channel_gid: str
) -> LinkProperties:
    if channel_gid == "destiniDash" or channel_gid == "destiniMinecraft":
        props = LinkProperties()
        channel_props = get_default_channel_properties_for_channel(sdk, channel_gid)

        props.transmissionType = channel_props.transmissionType
        props.connectionType = channel_props.connectionType
        props.sendType = channel_props.sendType
        props.reliable = channel_props.reliable
        props.duration_s = channel_props.duration_s
        props.period_s = channel_props.period_s
        props.mtu = channel_props.mtu

        worst_link_prop_set = LinkPropertySet()
        worst_link_prop_set.bandwidth_bps = 100000
        worst_link_prop_set.latency_ms = 2000
        worst_link_prop_set.loss = -1.0
        props.worst.send = worst_link_prop_set
        props.worst.receive = worst_link_prop_set

        props.expected = channel_props.creatorExpected

        best_link_prop_set = LinkPropertySet()
        best_link_prop_set.bandwidth_bps = 3000000
        best_link_prop_set.latency_ms = 500
        best_link_prop_set.loss = -1.0
        props.best.send = best_link_prop_set
        props.best.receive = best_link_prop_set

        props.supported_hints = channel_props.supported_hints
        props.channelGid = channel_gid

        return props


    if channel_gid == "destiniPixelfed" or channel_gid == "destiniAvideo":
        props = LinkProperties()

        channel_props = get_default_channel_properties_for_channel(sdk, channel_gid)
        props.transmissionType = channel_props.transmissionType
        props.connectionType = channel_props.connectionType
        props.sendType = channel_props.sendType
        props.reliable = channel_props.reliable
        props.duration_s = channel_props.duration_s
        props.period_s = channel_props.period_s
        props.mtu = channel_props.mtu

        worst_link_prop_set = LinkPropertySet()
        best_link_prop_set = LinkPropertySet()
        

        if channel_gid == "destiniPixelfed":
            worst_link_prop_set.bandwidth_bps = 2000
            worst_link_prop_set.latency_ms = 6000
            best_link_prop_set.bandwidth_bps = 15000
            best_link_prop_set.latency_ms = 1800
        else:
            worst_link_prop_set.bandwidth_bps = 50000
            worst_link_prop_set.latency_ms = 10000
            best_link_prop_set.bandwidth_bps = 200000
            best_link_prop_set.latency_ms = 2800
            

        best_link_prop_set.loss = 0.1
        worst_link_prop_set.loss = 0.1
        props.worst.send = worst_link_prop_set
        props.worst.receive = worst_link_prop_set

        props.expected = channel_props.creatorExpected

        props.best.send = best_link_prop_set
        props.best.receive = best_link_prop_set

        props.supported_hints = channel_props.supported_hints
        props.channelGid = channel_gid

        return props

    raise Exception(
        f"get_default_link_properties_for_channel: invalid channel GID: {channel_gid}"
    )
