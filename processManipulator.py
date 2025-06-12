"""
Tool for manipulation system windows.

You can either create a WindowManipulator and
do as you will with it, or derive from WindowManipulator
with a member called hwnd, that the manipulator will operate on.
"""
import typing
import os
from pathlib import Path
import psutil
if os.name=='nt':
    import win32gui


def pidToHwnds(pid:int)->typing.Iterable[str]:
    """
    Get all top-level window handles for a process id
    """
    if os.name=='nt':
        import win32process
        hwnds=[]
        def cb(hwnd,hwnds):
            _,windowPid=win32process.GetWindowThreadProcessId(hwnd)
            if windowPid==pid:
                hwnds.append(hwnd)
        win32gui.EnumWindows(cb,hwnds)
    else:
        raise NotImplementedError('Need to implement for this os')
    return hwnds


def pidToHwnd(pid:int)->str:
    """
    Get the main window handle for a process id

    If the pid has no associated windows, could throw IndexError
    """
    hwnds=pidToHwnds(pid)
    return hwnds[0] # this could throw IndexError, but that's what we want


def allSystemProcesses()->typing.Generator["ProcessManipulator",None,None]:
    """
    Go through all system processes
    """
    for pid in psutil.pids():
        yield ProcessManipulator(pid)


def findSystemProcesses(
    cmdline:typing.Union[None,
        str,Path,typing.Pattern,typing.Iterable[str],"ProcessManipulator"],
    hasNetworkPortOpen:typing.Union[None,int,typing.Iterable[int],bool]=None,
    hasFileOpen:typing.Union[
        None,str,Path,typing.Iterable[typing.Union[str,Path]]]=None
    )->typing.Iterable["ProcessManipulator"]:
    """
    Find all system processes that match
    """
    for proc in allSystemProcesses():
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


class ProcessManipulator(psutil.Process):
    """
    Tool for manipulation system processes.

    You can either create a ProcessManipulator and
    do as you will with it, or derive from ProcessManipulator
    with a member called pid, that the manipulator will operate on.

    TODO: I feel like I want to have the pid be more dynamic
    like it is pulled from the variable every time it is needed.
    Only time and testing will tell whether this is suitable as-is.
    """

    def __init__(self,
        pid:typing.Union[None,int,str]=None):
        """ """
        psutil.Process.__init__(pid)
        self.pid:typing.Union[int,None]=None
        if pid is not None:
            self.pid=int(pid)

    def cmdlineMatches(self,
        other:typing.Union[
            str,Path,typing.Pattern,typing.Iterable[str],"ProcessManipulator"]
        )->bool:
        """
        Test if the command line for this process matches a given
        executable name, regex, or all commandline parameters
        """
        if isinstance(other,ProcessManipulator):
            other=other.cmdline
        if isinstance(other,(str,Path)):
            if isinstance(other,str):
                other=Path(os.path.expandvars(other)).absolute()
            return Path(self.exe)==other
        if hasattr(other,'match'):
            return other.match(self.exe)
        isSame=True
        for e1,e2 in other,self.cmdline:
            if e1!=e2:
                isSame=False
                break
        return isSame

    def __int__(self)->int:
        return self.pid

    def __eq__(self,
        other:typing.Union[int,
            str,Path,typing.Pattern,typing.Iterable[str],"ProcessManipulator"]
        )->bool:
        """ """
        if isinstance(other,int):
            return other==self.pid
        if isinstance(other,str):
            try:
                other=int(other)
                return other==self.pid
            except Exception:
                pass
        return self.cmdlineMatches(other)

    def hasNetworkPortOpen(self,
        hasNetworkPortOpen:typing.Union[int,typing.Iterable[int],bool]=True
        )->bool:
        """
        Determine whether this process has
        (one of) the given network port(s) open

        :hasNetworkPortOpen: can be
            a single port number to test that it has open
            a list of port numbers to test if any are open
            True if you want to ensure there is a network port open
            False if you want to ensure there is not a network port open
        """
        for connInfo in self.connections():
            if connInfo[2] in ('inet4','tcp4','udp4'):
                port=int(connInfo[3].rsplit(':')[-1])
            elif connInfo[2] in ('inet6','tcp6','udp6'):
                raise NotImplementedError(connInfo[3])
            else:
                continue
            if isinstance(hasNetworkPortOpen,bool):
                return hasNetworkPortOpen
            elif isinstance(hasNetworkPortOpen,int):
                hasNetworkPortOpen=(hasNetworkPortOpen,)
            if port in hasNetworkPortOpen:
                return True
        if isinstance(hasNetworkPortOpen,bool):
            return not hasNetworkPortOpen
        return False

    def hasFileOpen(self,
        files:typing.Union[str,Path,typing.Iterable[typing.Union[str,Path]]]
        )->bool:
        """
        Check to see if the process has given file(s) open
        """
        if isinstance(files,str):
            files=Path(os.path.expandvars(files)).absolute()
        if isinstance(files,Path):
            files=(str(files),)
        else:
            files=[os.path.abspath(os.path.expandvars(str(f))) for f in files]
        for file in self.open_files():
            if file.path in files:
                return True
        return False

    def getProcessHwnds(self)->typing.Iterable[str]:
        """
        Get all top-level windows associated with
        the process being debugged
        """
        return pidToHwnds(self.pid)
    @property
    def hwnds(self)->typing.Iterable[str]:
        """
        Get all top-level windows associated with
        the process being debugged
        """
        return self.getProcessHwnds()

    def getProcessHwnd(self)->str:
        """
        Get main top-level window associated with
        the process being debugged

        Can throw IndexError if there is no window.
        """
        return pidToHwnds(self.pid)[0]
    @property
    def hwnd(self)->str:
        """
        Get the main top-level window associated with
        the process being debugged

        Can throw IndexError if there is no window.
        """
        return self.getProcessHwnd()
