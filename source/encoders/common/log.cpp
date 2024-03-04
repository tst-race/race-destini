#include "log.h"

static const std::string pluginNameForLogging = "PluginCommsTwoSixDecomposedCpp";

void logDebug(const std::string &message) {
    RaceLog::logDebug(pluginNameForLogging, message, "");
}

void logInfo(const std::string &message) {
    RaceLog::logInfo(pluginNameForLogging, message, "");
}

void logWarning(const std::string &message) {
    RaceLog::logWarning(pluginNameForLogging, message, "");
}

void logError(const std::string &message) {
    RaceLog::logError(pluginNameForLogging, message, "");
}
