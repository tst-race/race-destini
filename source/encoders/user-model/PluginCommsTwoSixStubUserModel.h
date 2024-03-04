#ifndef __COMMS_TWOSIX_USER_MODEL_H__
#define __COMMS_TWOSIX_USER_MODEL_H__

#include <IUserModelComponent.h>

#include <atomic>
#include <memory>
#include <mutex>
#include <set>
#include <unordered_map>

class LinkUserModel;

class PluginCommsTwoSixStubUserModel : public IUserModelComponent {
public:
    explicit PluginCommsTwoSixStubUserModel(IUserModelSdk *sdk);

    virtual ComponentStatus onUserInputReceived(RaceHandle handle, bool answered,
                                                const std::string &response) override;

    virtual UserModelProperties getUserModelProperties() override;

    virtual ComponentStatus addLink(const LinkID &link, const LinkParameters &params) override;

    virtual ComponentStatus removeLink(const LinkID &link) override;

    virtual ActionTimeline getTimeline(Timestamp start, Timestamp end) override;

    virtual ComponentStatus onTransportEvent(const Event &event) override;

protected:
    virtual std::shared_ptr<LinkUserModel> createLinkUserModel(const LinkID &linkId);

private:
    IUserModelSdk *sdk;

    std::mutex mutex;
    std::unordered_map<LinkID, std::shared_ptr<LinkUserModel>> linkUserModels;

    std::atomic<uint64_t> nextActionId{0};

    // TODO remove this when ComponentManager doesn't require the first action to have not changed
    // between generation of timelines
    std::set<LinkID> addedLinks;
};

#endif  // __COMMS_TWOSIX_USER_MODEL_H__