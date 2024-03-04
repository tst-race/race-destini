#include "LinkUserModel.h"

#include "JsonTypes.h"

static const double WAIT_TIME = 1.0;

LinkUserModel::LinkUserModel(const LinkID &linkId, std::atomic<uint64_t> &nextActionId) :
    linkId(linkId), nextActionId(nextActionId) {}

MarkovModel::UserAction LinkUserModel::getNextUserAction() {
    return model.getNextUserAction();
}

ActionType convertUserActionToActionType(MarkovModel::UserAction userAction) {
    switch (userAction) {
        case MarkovModel::UserAction::FETCH:
            return ACTION_FETCH;
        case MarkovModel::UserAction::POST:
            return ACTION_POST;
        default:
            return ACTION_UNDEF;
    }
}

ActionTimeline LinkUserModel::getTimeline(Timestamp start, Timestamp end) {
    // First, remove all actions from the cached timeline that occur before the `start` time
    auto iter = std::find_if(cachedTimeline.begin(), cachedTimeline.end(),
                             [start](const auto &val) { return val.timestamp >= start; });
    cachedTimeline.erase(cachedTimeline.begin(), iter);

    Timestamp current = start;
    // If we still have cached actions, start at the timestamp of the last action
    if (not cachedTimeline.empty()) {
        current = cachedTimeline.back().timestamp;
    }

    // Then add new actions to the timeline until we reach the `end` time
    while (current < end) {
        auto action = getNextUserAction();
        if (action == MarkovModel::UserAction::WAIT) {
            current += WAIT_TIME;
        } else {
            nlohmann::json actionJson = ActionJson{
                linkId,
                convertUserActionToActionType(action),
            };
            cachedTimeline.push_back({
                current,
                ++nextActionId,
                actionJson.dump(),
            });
        }
    }

    return cachedTimeline;
}