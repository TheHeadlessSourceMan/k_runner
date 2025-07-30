"""
Tools to find processes
"""
import typing
import os
from pathlib import Path
import psutil
if os.name=='nt':
    import win32process # type: ignore
    import win32gui # type: ignore
from k_runner.ui.windowHandleType import WindowHandleType # pylint: disable = wrong-import-position # noqa:E501
from .process import Process # pylint: disable = wrong-import-position


def allSystemProcesses()->typing.Generator[Process,None,None]:
    """
    Go through all system processes
    """
    for pid in psutil.pids():
        yield Process(pid)


def findSystemProcesses(
    processName:typing.Union[None,str,typing.Pattern[str],Process]=None,
    cmdline:typing.Union[None,
        str,Path,typing.Pattern[str],typing.Iterable[str],Process]=None,
    hasNetworkPortOpen:typing.Union[None,int,typing.Iterable[int],bool]=None,
    hasFileOpen:typing.Union[
        None,str,Path,typing.Iterable[typing.Union[str,Path]]]=None
    )->typing.Iterable[Process]:
    """
    Find all system processes that match
    """
    for proc in allSystemProcesses():
        # match the process name
        if processName is not None:
            if not proc.processNameMatches(processName):
                continue
        # match the command line
        if cmdline is not None:
            if not proc.cmdlineMatches(cmdline):
                continue
        # match by network port
        if hasNetworkPortOpen is not None:
            if not proc.hasNetworkPortOpen(hasNetworkPortOpen):
                continue
        # match by file
        if hasFileOpen is not None:
            if not proc.hasFileOpen(hasFileOpen):
                continue
        # Looks good!
        yield proc


def getHwndsByPid(
    pid:int,
    visibleOnly:bool=True
    )->typing.Iterable["WindowHandleType"]:
    """
    Gets any and all top-level windows of a process by pid

    :visibleOnly: whether to exclude invisible windows (default is True)

    TODO: currently works on windows only
    """
    found:typing.List[WindowHandleType]=[]
    if os.name=='nt':
        def enumWindowsCB(hwnd:WindowHandleType,pid:int):
            _,foundPid=win32process.GetWindowThreadProcessId(hwnd)
            if pid==foundPid \
                and (win32gui.IsWindowVisible(hwnd) \
                or not visibleOnly):
                #
                found.append(hwnd)
        win32gui.EnumWindows(enumWindowsCB,pid)
    else:
        raise NotImplementedError()
    return found
pidToHwnds=getHwndsByPid


def getHwndByPid(
    pid:int,
    visibleOnly:bool=True
    )->typing.Optional[WindowHandleType]:
    """
    Gets main top-level window of a process by pid

    :visibleOnly: whether to exclude invisible windows (default is True)
    """
    for hwnd in getHwndsByPid(pid,visibleOnly):
        return hwnd
    return None
pidToHwnd=getHwndByPid


def getPidByHwnd(hwnd:WindowHandleType)->int:
    """
    Gets pid of a window

    TODO: currently works on windows only
    """
    _,foundPid=win32process.GetWindowThreadProcessId(hwnd)
    return foundPid
hwndToPid=getPidByHwnd


def findProcesses(
    programName:typing.Union[None,str,typing.Pattern[str]]=None
    )->typing.Generator[Process,None,None]:
    """
    search for running processes that match the given parameters
    (or all, if no parameters given)

    :programName: can be a string that the executable name ends with,
        or a regex to match on.
    """
    if programName is None:
        for pid in win32process.EnumProcesses():
            yield Process(pid)
    elif isinstance(programName,str):
        for pid in win32process.EnumProcesses():
            p=Process(pid)
            if p.name.endswith(programName):
                yield p
    else:
        for pid in win32process.EnumProcesses():
            p=Process(pid)
            if programName.match(p.name) is not None:
                yield p


def findProcess(
    programName:typing.Union[None,str,typing.Pattern[str]]=None
    )->typing.Optional[Process]:
    """
    Exactly like findProcesses(), but returns only one (or none)
    """
    for p in findProcesses(programName):
        return p
    return None


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    didSomething=False
    printHelp=False
    currentProcesses:typing.List[Process]=[]
    for arg in args:
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-h','--help'):
                printHelp=True
            elif av[0]=='--findprocess':
                if len(av)>1:
                    p=findProcess(av[1])
                else:
                    p=findProcess()
                print(p)
                if p is None:
                    currentProcesses=[]
                else:
                    currentProcesses=[p]
                didSomething=True
            elif av[0]=='--findprocesses':
                if len(av)>1:
                    currentProcesses=list(findProcesses(av[1]))
                else:
                    currentProcesses=list(findProcesses())
                if not currentProcesses:
                    print(None)
                for p in currentProcesses:
                    print(p)
                didSomething=True
            else:
                printHelp=True
        else:
            printHelp=True
    if printHelp or not didSomething:
        print('USAGE:')
        print('  processPlayset [commands]')
        print('NOTE:')
        print('  commands are evaluated in order')
        print('OPTIONS:')
        print('  -h ................................. this help')
        print('  --findProcess[=endswith] ........... find a process that')
        print('                   ends with the executable name')
        print('  --findProcesses[=endswith] ......... find all processes that')
        print('                   ends with the executable name')
        return 1
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
