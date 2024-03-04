#include "PluginCommsTwoSixNoopEncoding.h"

#include "log.h"

const char *PluginCommsTwoSixNoopEncoding::name = "noop";

PluginCommsTwoSixNoopEncoding::PluginCommsTwoSixNoopEncoding(IEncodingSdk *_sdk) : sdk(_sdk) {
    if (this->sdk == nullptr) {
        throw std::runtime_error("PluginCommsTwoSixNoopEncoding: sdk parameter is NULL");
    }
    sdk->updateState(COMPONENT_STATE_STARTED);
}

ComponentStatus PluginCommsTwoSixNoopEncoding::onUserInputReceived(RaceHandle handle, bool answered,
                                                                 const std::string &response) {
    TRACE_METHOD(handle, answered, response);

    return COMPONENT_OK;
}

EncodingProperties PluginCommsTwoSixNoopEncoding::getEncodingProperties() {
    TRACE_METHOD();

    return {0, "application/octet-stream"};
}

SpecificEncodingProperties PluginCommsTwoSixNoopEncoding::getEncodingPropertiesForParameters(
    const EncodingParameters & /* params */) {
    TRACE_METHOD();

    return {1000000};
}

ComponentStatus PluginCommsTwoSixNoopEncoding::encodeBytes(RaceHandle handle,
                                                         const EncodingParameters &params,
                                                         const std::vector<uint8_t> &bytes) {
    TRACE_METHOD(handle, params.linkId, params.type, params.encodePackage, params.json);

    // TODO: do I need to thread this? Or should I just for exemplary sake?
    sdk->onBytesEncoded(handle, bytes, ENCODE_OK);

    return COMPONENT_OK;
}

ComponentStatus PluginCommsTwoSixNoopEncoding::decodeBytes(RaceHandle handle,
                                                         const EncodingParameters &params,
                                                         const std::vector<uint8_t> &bytes) {
    TRACE_METHOD(handle, params.linkId, params.type, params.encodePackage, params.json);

    // TODO: do I need to thread this? Or should I just for exemplary sake?
    sdk->onBytesDecoded(handle, bytes, ENCODE_OK);

    return COMPONENT_OK;
}
