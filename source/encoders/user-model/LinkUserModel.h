#ifndef __COMMS_TWOSIX_USER_MODEL_LINK_USER_MODEL_H__
#define __COMMS_TWOSIX_USER_MODEL_LINK_USER_MODEL_H__

#include <ComponentTypes.h>

#include <atomic>

#include "MarkovModel.h"

class LinkUserModel {
public:
    explicit LinkUserModel(const LinkID &linkId, std::atomic<uint64_t> &nextActionId);
    virtual ~LinkUserModel() {}

    /**
     * @brief Get the action timeline for this link between the specified start and end timestamps.
     *
     * @param start Timestamp at which to start
     * @param end Timestamp at which to end
     * @return Action timeline
     */
    virtual ActionTimeline getTimeline(Timestamp start, Timestamp end);

protected:
    virtual MarkovModel::UserAction getNextUserAction();

private:
    MarkovModel model;
    LinkID linkId;
    std::atomic<uint64_t> &nextActionId;
    ActionTimeline cachedTimeline;
};

#endif  // __COMMS_TWOSIX_USER_MODEL_LINK_USER_MODEL_H__