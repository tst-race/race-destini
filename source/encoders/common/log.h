#ifndef __COMMS_TWOSIX_COMMON_LOG_H__
#define __COMMS_TWOSIX_COMMON_LOG_H__

#include <RaceLog.h>

#include <string>

void logDebug(const std::string &message);
void logInfo(const std::string &message);
void logWarning(const std::string &message);
void logError(const std::string &message);

#define TRACE_METHOD(...) TRACE_METHOD_BASE(PluginCommsTwoSixDecomposedCpp, ##__VA_ARGS__)
#define TRACE_FUNCTION(...) TRACE_FUNCTION_BASE(PluginCommsTwoSixDecomposedCpp, ##__VA_ARGS__)

#endif  // __COMMS_TWOSIX_COMMON_LOG_H__
