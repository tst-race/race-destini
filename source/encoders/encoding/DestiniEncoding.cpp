#include "DestiniEncoding.h"

#include <cstdlib>
#include <fstream>
#include <sys/stat.h>
#include <string>
#include <vector>

#include "log.h"


const char *DestiniEncoding::name = "DestiniEncoding";


DestiniEncoding::DestiniEncoding(IEncodingSdk *_sdk, const PluginConfig &_pluginConfig) : sdk(_sdk), pluginConfig(_pluginConfig) {
    if (this->sdk == nullptr) {
        throw std::runtime_error ("DestiniEncoding: sdk parameter is NULL");
    }

    this->cliCodec = nullptr;

#if 0
    if (this->pluginConfig.pluginDirectory.length () /* > 0 */)
      CLICodec::SetDirname ("/usr/local/lib/race/comms/DestiniDecomposed");
    else
#endif
    CLICodec::SetDirname (this->pluginConfig.pluginDirectory);

    // Get codec definition

    auto codecJSONPath = CLICodec::DirFilename ("codec.json");
    auto codecJSON     = codecJSONPath.c_str ();

    if (fileExists (codecJSON)) {
         std::ifstream fJSON (codecJSON);
         cliCodec = CLICodec::GetCodecFromStream (fJSON);
         if (cliCodec == nullptr || !cliCodec->isGood ())
             throw std::runtime_error ("DestiniEncoding: bad or incomplete JSON (" + codecJSONPath + ")");
    }
    else
        throw std::runtime_error ("DestiniEncoding: JSON (" + codecJSONPath + ") not found");

    sdk->updateState(COMPONENT_STATE_STARTED);
}

ComponentStatus DestiniEncoding::onUserInputReceived(RaceHandle handle, bool answered,
                                                             const std::string &response) {
    TRACE_METHOD(handle, answered, response);

    return COMPONENT_OK;
}

EncodingProperties DestiniEncoding::getEncodingProperties() {
    TRACE_METHOD();

    return {cliCodec->encodingTime (), cliCodec->mimeType ()};
}

SpecificEncodingProperties DestiniEncoding::getEncodingPropertiesForParameters(
    const EncodingParameters & /* params */) {
    TRACE_METHOD();

    return {static_cast <int32_t> (cliCodec->maxCapacity ())};
}

ComponentStatus DestiniEncoding::encodeBytes(RaceHandle handle,
                                                     const EncodingParameters &params,
                                                     const std::vector<uint8_t> &bytes) {
    TRACE_METHOD(handle, params.linkId, params.type, params.encodePackage, params.json);

    // Per https://github.com/redboltz/mqtt_cpp/issues/854
    auto   *pMsgIn = bytes.data ();
    size_t  nMsgIn = bytes.size ();

    logInfo ("DestiniEncoding::encodeBytes, nMsgIn: " + std::to_string (nMsgIn));

    if (nMsgIn == 0) {
    	sdk->onBytesEncoded (handle, bytes, ENCODE_OK);
		return COMPONENT_OK;
    }

    char   *pMsgOut;
    size_t  nMsgOut;

    if (cliCodec->encode (pMsgIn, nMsgIn, reinterpret_cast <void **> (&pMsgOut), &nMsgOut) /* != 0 */) {
        sdk->onBytesEncoded (handle, {}, ENCODE_FAILED);

        return COMPONENT_ERROR;
    }
    else {
        // Per https://www.appsloveworld.com/cplus/100/1168/convert-unsigned-char-into-stdvectoruint8-t
        std::vector<uint8_t> encodedBytes (pMsgOut, pMsgOut + nMsgOut);
        free (pMsgOut);

        sdk->onBytesEncoded (handle, encodedBytes, ENCODE_OK);

        return COMPONENT_OK;
    }
}

ComponentStatus DestiniEncoding::decodeBytes(RaceHandle handle,
                                                     const EncodingParameters &params,
                                                     const std::vector<uint8_t> &bytes) {
    TRACE_METHOD(handle, params.linkId, params.type, params.encodePackage, params.json);

    // Per https://github.com/redboltz/mqtt_cpp/issues/854
    auto   *pMsgIn = bytes.data ();
    size_t  nMsgIn = bytes.size ();
    char   *pMsgOut;
    size_t  nMsgOut;

    if (cliCodec->decode (pMsgIn, nMsgIn, reinterpret_cast <void **> (&pMsgOut), &nMsgOut) /* != 0 */) {
        sdk->onBytesDecoded (handle, {}, ENCODE_FAILED);

        return COMPONENT_ERROR;
    }
    else {
        // Per https://www.appsloveworld.com/cplus/100/1168/convert-unsigned-char-into-stdvectoruint8-t
        std::vector<uint8_t> decodedBytes (pMsgOut, pMsgOut + nMsgOut);
        free (pMsgOut);

        sdk->onBytesDecoded (handle, decodedBytes, ENCODE_OK);

        return COMPONENT_OK;
    }
}
