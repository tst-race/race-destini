#include "LinkMap.h"

int LinkMap::size() const {
    std::lock_guard<std::mutex> lock(mutex);
    return links.size();
}

void LinkMap::clear() {
    std::lock_guard<std::mutex> lock(mutex);
    links.clear();
}

void LinkMap::add(const std::shared_ptr<Link> &link) {
    std::lock_guard<std::mutex> lock(mutex);
    links[link->getId()] = link;
}

std::shared_ptr<Link> LinkMap::get(const LinkID &linkId) const {
    std::lock_guard<std::mutex> lock(mutex);
    return links.at(linkId);
}

std::shared_ptr<Link> LinkMap::remove(const LinkID &linkId) {
    std::lock_guard<std::mutex> lock(mutex);
    std::shared_ptr<Link> value;
    auto iter = links.find(linkId);
    if (iter != links.end()) {
        value = iter->second;
        links.erase(iter);
    }
    return value;
}