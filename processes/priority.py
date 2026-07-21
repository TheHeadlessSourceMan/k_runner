"""
Tools for managing priority
"""
import os


if os.name=='nt':
    from .windowsPriority import (
        getWindowsPriorityCode,getWindowsPriorityName)
    getPriorityCode=getWindowsPriorityCode
    getPriorityName=getWindowsPriorityName
else:
    def getPriorityCode(pri:int)->int:
        """
        note that windows priority codes are
        different, but most systems would probably
        just be the same as the priority itself
        """
        return pri

    def getPriorityName(priority:float)->str:
        """
        For the start.exe command
        """
        from .priorityConstants import (
            BELOW_NORMAL_PRIORITY,
            NORMAL_PRIORITY,
            ABOVE_NORMAL_PRIORITY,
            HIGH_PRIORITY,
            REALTIME_PRIORITY)
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
