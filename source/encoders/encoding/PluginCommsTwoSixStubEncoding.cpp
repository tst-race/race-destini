#include <IEncodingComponent.h>
#include <string.h>  // strcmp

#include "PluginCommsTwoSixBase64Encoding.h"
#include "PluginCommsTwoSixNoopEncoding.h"
#include "DestiniEncoding.h"
#include "log.h"

#ifndef TESTBUILD
IEncodingComponent *createEncoding(const std::string &encoding, IEncodingSdk *sdk,
                                   const std::string &roleName,
                                   const PluginConfig &pluginConfig) {
    TRACE_FUNCTION(encoding, roleName);

    if (sdk == nullptr) {
        RaceLog::logError(logPrefix, "`sdk` parameter is set to NULL.", "");
        return nullptr;
    }

    if (encoding == PluginCommsTwoSixNoopEncoding::name) {
        return new PluginCommsTwoSixNoopEncoding(sdk);
    } else if (encoding == PluginCommsTwoSixBase64Encoding::name) {
        return new PluginCommsTwoSixBase64Encoding(sdk);
    } else if (encoding == DestiniEncoding::name) {
        return new DestiniEncoding(sdk, pluginConfig);
    } else {
        RaceLog::logError(logPrefix, "invalid encoding type: " + std::string(encoding), "");
        return nullptr;
    }
}
void destroyEncoding(IEncodingComponent *component) {
    TRACE_FUNCTION();
    delete component;
}

const RaceVersionInfo raceVersion = RACE_VERSION;
#endif
