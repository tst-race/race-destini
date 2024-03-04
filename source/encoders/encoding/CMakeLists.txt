################################################################################
# Encoding component
################################################################################

setup_component_target(
    TARGET DestiniEncoding
    SOURCES
        DestiniEncoding.cpp
        CLICodec.cpp
        StringUtility.cpp
        ../common/log.cpp
        PluginCommsTwoSixBase64Encoding.cpp
        PluginCommsTwoSixNoopEncoding.cpp
        PluginCommsTwoSixStubEncoding.cpp
)
