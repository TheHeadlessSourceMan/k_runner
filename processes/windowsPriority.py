"""
Process priority functions for windows
"""


from processes.priorityConstants import (
    BELOW_NORMAL_PRIORITY,
    NORMAL_PRIORITY,
    ABOVE_NORMAL_PRIORITY,
    HIGH_PRIORITY,
    REALTIME_PRIORITY)


def getWindowsPriorityCode(pri:int)->int:
    """
    weirdly the values for windows priority
    codes don't follow any real pattern
    that I can see.
    """
    if pri<BELOW_NORMAL_PRIORITY:
        return 64
    if pri<NORMAL_PRIORITY:
        return 16384
    if pri<ABOVE_NORMAL_PRIORITY:
        return 32
    if pri<HIGH_PRIORITY:
        return 32768
    if pri<REALTIME_PRIORITY:
        return 128
    return 256

def getWindowsWmicPriority(pri:int)->str:
    """
    for the wmic.exe command
    """
    if pri<BELOW_NORMAL_PRIORITY:
        return 'Low'
    if pri<NORMAL_PRIORITY:
        return 'Below normal'
    if pri<ABOVE_NORMAL_PRIORITY:
        return 'Normal'
    if pri<HIGH_PRIORITY:
        return 'Above normal'
    if pri<REALTIME_PRIORITY:
        return 'High'
    return 'Realtime'

def getWindowsPriorityName(priority:float)->str:
    """
    For the start.exe command
    """
    if priority<BELOW_NORMAL_PRIORITY:
        return 'Low'
    if priority<NORMAL_PRIORITY:
        return 'BelowNormal'
    if priority<ABOVE_NORMAL_PRIORITY:
        return 'Normal'
    if priority<HIGH_PRIORITY:
        return 'AboveNormal'
    if priority<REALTIME_PRIORITY:
        return 'High'
    return 'Realtime'
