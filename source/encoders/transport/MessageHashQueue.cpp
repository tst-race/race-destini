#include "MessageHashQueue.h"

#include <algorithm>
#include <string>

std::size_t MessageHashQueue::hash(const std::string &message) {
    return std::hash<std::string>()({message.begin(), message.end()});
}

std::size_t MessageHashQueue::addMessage(const std::string &message) {
    if (queue.size() > max) {
        queue.pop_front();
    }
    auto msgHash = hash(message);
    queue.push_back(msgHash);
    return msgHash;
}

void MessageHashQueue::removeHash(std::size_t hash) {
    auto iter = std::find(queue.begin(), queue.end(), hash);
    if (iter != queue.end()) {
        queue.erase(iter);
    }
}

bool MessageHashQueue::findAndRemoveMessage(const std::string &message) {
    auto iter = std::find(queue.begin(), queue.end(), hash(message));
    bool found = iter != queue.end();
    if (found) {
        queue.erase(queue.begin(), iter + 1);
    }
    return found;
}