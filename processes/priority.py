"""
Tools for managing priority
"""

# my priority codes (in decimal percent)
# 0.0=lowest, 1.0=highest, >1.0 is realtime (which is usually a bad idea)
LOWEST_PRIORITY=0
LOW_PRIORITY=0
LOWER_PRIORITY=0.25
BELOW_NORMAL_PRIORITY=0.25
NORMAL_PRIORITY=0.50
MEDIUM_PRIORITY=0.50
ABOVE_NORMAL_PRIORITY=0.75
HIGHER_PRIORITY=0.75
HIGH_PRIORITY=1.00
HIGHEST_PRIORITY=1.00
REALTIME_PRIORITY=1.01


def _getWindowsPriorityCode(pri:int)->int:
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

def _getWindowsWmicPriority(pri:int)->str:
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

def _getWindowsPriorityName(priority:float)->str:
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
