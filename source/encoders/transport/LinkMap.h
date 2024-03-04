#ifndef __COMMS_TWOSIX_TRANSPORT_LINK_MAP_H__
#define __COMMS_TWOSIX_TRANSPORT_LINK_MAP_H__

#include <memory>
#include <mutex>
#include <unordered_map>

#include "Link.h"

class LinkMap {
public:
    int size() const;
    void clear();
    void add(const std::shared_ptr<Link> &link);
    std::shared_ptr<Link> get(const LinkID &linkId) const;
    std::shared_ptr<Link> remove(const LinkID &linkId);

private:
    mutable std::mutex mutex;
    std::unordered_map<LinkID, std::shared_ptr<Link>> links;
};

#endif  // __COMMS_TWOSIX_TRANSPORT_LINK_MAP_H__