################################################################################
# Transport component
################################################################################

setup_component_target(
    TARGET PluginCommsTwoSixStubTransport
    SOURCES
        Link.cpp
        LinkAddress.cpp
        LinkMap.cpp
        MessageHashQueue.cpp
        PluginCommsTwoSixStubTransport.cpp
        ../common/log.cpp
)
