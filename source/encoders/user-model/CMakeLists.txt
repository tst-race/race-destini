################################################################################
# User Model component
################################################################################

setup_component_target(
    TARGET PluginCommsTwoSixStubUserModel
    SOURCES
        LinkUserModel.cpp
        MarkovModel.cpp
        PluginCommsTwoSixStubUserModel.cpp
        ../common/log.cpp
)
