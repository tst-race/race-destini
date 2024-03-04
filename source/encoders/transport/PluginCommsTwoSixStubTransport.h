#ifndef __COMMS_TWOSIX_TRANSPORT_H__
#define __COMMS_TWOSIX_TRANSPORT_H__

#include <ChannelProperties.h>
#include <ITransportComponent.h>
#include <LinkProperties.h>

#include <atomic>

#include "LinkMap.h"

class PluginCommsTwoSixStubTransport : public ITransportComponent {
public:
    explicit PluginCommsTwoSixStubTransport(ITransportSdk *sdk);

    virtual ComponentStatus onUserInputReceived(RaceHandle handle, bool answered,
                                                const std::string &response) override;

    virtual TransportProperties getTransportProperties() override;

    virtual LinkProperties getLinkProperties(const LinkID &linkId) override;

    virtual ComponentStatus createLink(RaceHandle handle, const LinkID &linkId) override;

    virtual ComponentStatus loadLinkAddress(RaceHandle handle, const LinkID &linkId,
                                            const std::string &linkAddress) override;

    virtual ComponentStatus loadLinkAddresses(RaceHandle handle, const LinkID &linkId,
                                              const std::vector<std::string> &linkAddress) override;

    virtual ComponentStatus createLinkFromAddress(RaceHandle handle, const LinkID &linkId,
                                                  const std::string &linkAddress) override;

    virtual ComponentStatus destroyLink(RaceHandle handle, const LinkID &linkId) override;

    virtual std::vector<EncodingParameters> getActionParams(const Action &action) override;

    virtual ComponentStatus enqueueContent(const EncodingParameters &params, const Action &action,
                                           const std::vector<uint8_t> &content) override;

    virtual ComponentStatus dequeueContent(const Action &action) override;

    virtual ComponentStatus doAction(const std::vector<RaceHandle> &handles,
                                     const Action &action) override;

protected:
    virtual std::shared_ptr<Link> createLinkInstance(const LinkID &linkId,
                                                     const LinkAddress &address,
                                                     const LinkProperties &properties);

private:
    ITransportSdk *sdk;
    std::string racePersona;
    ChannelProperties channelProperties;
    LinkProperties defaultLinkProperties;

    LinkMap links;

    // Next available hashtag suffix.
    // TODO: should probably pull from a pool of tags (randomly generated?) instead so we can reuse
    // old tags. Although I'm guessing with a 64 bit int it's unlikely this will ever rollover
    // (famous last words?) - GP
    std::atomic<int64_t> nextAvailableHashTag{0};

    bool preLinkCreate(const std::string &logPrefix, RaceHandle handle, const LinkID &linkId,
                       LinkSide invalidRoleLinkSide);
    ComponentStatus postLinkCreate(const std::string &logPrefix, RaceHandle handle,
                                   const LinkID &linkId, const std::shared_ptr<Link> &link,
                                   LinkStatus linkStatus);
};

#endif  // __COMMS_TWOSIX_TRANSPORT_H__