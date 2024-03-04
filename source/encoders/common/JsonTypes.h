#ifndef __COMMS_TWOSIX_COMMON_JSON_TYPES_H__
#define __COMMS_TWOSIX_COMMON_JSON_TYPES_H__

#include <nlohmann/json.hpp>
#include <string>

enum ActionType {
    ACTION_UNDEF,
    ACTION_FETCH,
    ACTION_POST,
};

NLOHMANN_JSON_SERIALIZE_ENUM(ActionType, {
                                             {ACTION_UNDEF, nullptr},
                                             {ACTION_FETCH, "fetch"},
                                             {ACTION_POST, "post"},
                                         });

struct ActionJson {
    std::string linkId;
    ActionType type;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(ActionJson, linkId, type);

struct EncodingParamsJson {
    int maxBytes;
};

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(EncodingParamsJson, maxBytes);

#endif  // __COMMS_TWOSIX_COMMON_JSON_TYPES_H__