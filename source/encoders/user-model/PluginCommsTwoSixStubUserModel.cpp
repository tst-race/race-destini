#include "PluginCommsTwoSixStubUserModel.h"

#include <algorithm>

#include "LinkUserModel.h"
#include "log.h"

PluginCommsTwoSixStubUserModel::PluginCommsTwoSixStubUserModel(IUserModelSdk *sdk) : sdk(sdk) {
    // No user input requests are needed, so user model is ready right away
    sdk->updateState(COMPONENT_STATE_STARTED);
}

ComponentStatus PluginCommsTwoSixStubUserModel::onUserInputReceived(RaceHandle handle, bool answered,
                                                                  const std::string &response) {
    TRACE_METHOD(handle, answered, response);
    // We don't make any user input requests
    return COMPONENT_OK;
}

UserModelProperties PluginCommsTwoSixStubUserModel::getUserModelProperties() {
    TRACE_METHOD();
    // TODO implement this
    return {};
}

std::shared_ptr<LinkUserModel> PluginCommsTwoSixStubUserModel::createLinkUserModel(
    const LinkID &linkId) {
    return std::make_shared<LinkUserModel>(linkId, nextActionId);
}

ComponentStatus PluginCommsTwoSixStubUserModel::addLink(const LinkID &link,
                                                      const LinkParameters & /* params */) {
    TRACE_METHOD(link);
    {
        std::lock_guard<std::mutex> lock(mutex);
        linkUserModels[link] = createLinkUserModel(link);
        addedLinks.insert(link);
    }
    sdk->onTimelineUpdated();
    return COMPONENT_OK;
}

ComponentStatus PluginCommsTwoSixStubUserModel::removeLink(const LinkID &link) {
    TRACE_METHOD(link);
    {
        std::lock_guard<std::mutex> lock(mutex);
        linkUserModels.erase(link);
    }
    sdk->onTimelineUpdated();
    return COMPONENT_OK;
}

ActionTimeline PluginCommsTwoSixStubUserModel::getTimeline(Timestamp start, Timestamp end) {
    TRACE_METHOD(start, end);
    std::lock_guard<std::mutex> lock(mutex);

    ActionTimeline timeline;
    Timestamp earliestTimestamp = std::numeric_limits<double>::max();
    for (auto &entry : linkUserModels) {
        // Skip recently added links for now
        if (addedLinks.find(entry.first) != addedLinks.end()) {
            continue;
        }
        auto linkTimeline = entry.second->getTimeline(start, end);
        earliestTimestamp = std::min(earliestTimestamp, linkTimeline.front().timestamp);
        timeline.insert(timeline.end(), linkTimeline.begin(), linkTimeline.end());
    }

    // Create timelines for recently added links, but adjust the start time so that they all occur
    // _after_ the first previously generated. The ComponentManager requires the first action in the
    // timeline to have not changed since the last time the timeline was generated, assuming
    // overlapping time windows.
    Timestamp timeAfterEarliestAction;
    if (earliestTimestamp == std::numeric_limits<double>::max()) {
        timeAfterEarliestAction = start;
    } else {
        timeAfterEarliestAction = earliestTimestamp + 1.0;
    }
    for (auto &linkId : addedLinks) {
        auto linkTimeline = linkUserModels.at(linkId)->getTimeline(timeAfterEarliestAction, end);
        timeline.insert(timeline.end(), linkTimeline.begin(), linkTimeline.end());
    }
    addedLinks.clear();

    std::sort(timeline.begin(), timeline.end(), [](const auto &lhs, const auto &rhs) {
        if (lhs.timestamp == rhs.timestamp) {
            return lhs.actionId < rhs.actionId;
        }
        return lhs.timestamp < rhs.timestamp;
    });

    return timeline;
}

ComponentStatus PluginCommsTwoSixStubUserModel::onTransportEvent(const Event & /* event */) {
    TRACE_METHOD();
    // We don't expect or react to any transport events
    return COMPONENT_OK;
}

#ifndef TESTBUILD
IUserModelComponent *createUserModel(const std::string &usermodel, IUserModelSdk *sdk,
                                     const std::string &roleName,
                                     const PluginConfig & /* pluginConfig */) {
    TRACE_FUNCTION(usermodel, roleName);
    return new PluginCommsTwoSixStubUserModel(sdk);
}
void destroyUserModel(IUserModelComponent *component) {
    TRACE_FUNCTION();
    delete component;
}

const RaceVersionInfo raceVersion = RACE_VERSION;
#endif