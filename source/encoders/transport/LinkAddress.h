#ifndef __COMMS_TWOSIX_TRANSPORT_LINK_PROFILE_H__
#define __COMMS_TWOSIX_TRANSPORT_LINK_PROFILE_H__

#include <nlohmann/json.hpp>
#include <string>

struct LinkAddress {
    // Required
    std::string hashtag;
    // Optional
    std::string hostname{"twosix-whiteboard"};
    int port{5000};
    int maxTries{120};
    double timestamp{-1.0};
};

// Enable automatic conversion to/from json
void to_json(nlohmann::json &destJson, const LinkAddress &srcLinkAddress);
void from_json(const nlohmann::json &srcJson, LinkAddress &destLinkAddress);

#endif  // __COMMS_TWOSIX_TRANSPORT_LINK_PROFILE_H__