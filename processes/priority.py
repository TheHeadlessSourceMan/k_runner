"""
Tools for managing priority
"""

# my priority codes (0-100) low-high
LOWEST_PRIORITY=0
LOW_PRIORITY=0
LOWER_PRIORITY=25
BELOW_NORMAL_PRIORITY=25
NORMAL_PRIORITY=50
MEDIUM_PRIORITY=50
ABOVE_NORMAL_PRIORITY=75
HIGHER_PRIORITY=75
HIGH_PRIORITY=100
HIGHEST_PRIORITY=100
REALTIME_PRIORITY=101

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

def _getWindowsPriorityName(pri:int)->str:
    """
    For the start.exe command
    """
    if pri<BELOW_NORMAL_PRIORITY:
        return 'Low'
    if pri<NORMAL_PRIORITY:
        return 'BelowNormal'
    if pri<ABOVE_NORMAL_PRIORITY:
        return 'Normal'
    if pri<HIGH_PRIORITY:
        return 'AboveNormal'
    if pri<REALTIME_PRIORITY:
        return 'High'
    return 'Realtime'
