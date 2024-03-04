"""
    Purpose:
        Helper functions for logging using the RaceLog functionality

    If you wish to use this file in your own project, make sure to change the
    plugin name in the logging functions to one specific to your project.
"""

from commsPluginBindings import RaceLog


def logDebug(message):
    """
    Purpose:
        A simplifying wrapper for RaceLog.logDebug
    """
    RaceLog.logDebug("Destini", message, "")


def logInfo(message):
    """
    Purpose:
        A simplifying wrapper for RaceLog.logInfo
    """
    RaceLog.logInfo("Destini", message, "")


def logWarning(message):
    """
    Purpose:
        A simplifying wrapper for RaceLog.logWarning
    """
    RaceLog.logWarning("PluginCommsTwoDestini", message, "")


def logError(message):
    """
    Purpose:
        A simplifying wrapper for RaceLog.logError
    """
    RaceLog.logError("Destini", message, "")
