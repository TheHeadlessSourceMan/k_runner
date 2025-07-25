"""
Tool for manipulation system processes.

You can either create a ProcessManipulator and
do as you will with it, or derive from ProcessManipulator
with a member called pid, that the manipulator will operate on.
"""
import typing
import os
from pathlib import Path
import psutil
if os.name=='nt':
    import win32api
    import win32process
    import win32con
    import pywintypes
try:
    import codeTools.debuggerManager as debuggerManager
    from codeTools import ProgramDebugInfo
    hasDebuggerManager=True
except ImportError:
    ProgramDebugInfo=typing.Any
    hasDebuggerManager=False
from .asProcess import ProcessCompatible # noqa: E402 # pylint: disable=wrong-import-position
if typing.TYPE_CHECKING:
    from k_runner.ui.window import Window
    from cmdline.commandLine import CommandLine


class Process(psutil.Process):
    """
    Tool for manipulation system processes.

    You can either create a ProcessManipulator and
    do as you will with it, or derive from ProcessManipulator
    with a member called pid, that the manipulator will operate on.

    TODO: I feel like I want to have the pid be more dynamic
    like it is pulled from the variable every time it is needed.
    Only time and testing will tell whether this is suitable as-is.
    """
    def __init__(self,pid:ProcessCompatible):
        if hasattr(pid,'process'):
            pid=pid.process # type: ignore
        if hasattr(pid,'pid'):
            pid=pid.pid # type: ignore
        pid=int(pid) # type: ignore
        psutil.Process.__init__(self,pid)
        self._name:typing.Optional[str]=None
        self._programDebugInfo:typing.Optional[typing.Any]=None

    @property
    def commandLineString(self)->str:
        """
        Get the command line used to start a process
        """
        wmiStyle=False
        if wmiStyle:
            # Requires the wmi module:
            # http://timgolden.me.uk/python/wmi/index.html
            import wmi # type: ignore # pylint: disable = import-error
            c=wmi.WMI()
            print(dir(c))
            #raise Exception()
            for process in c.Win32_Process():
                print(process.CommandLine)
        else:
            # use powershell
            # see also:
            # https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process?view=net-5.0#properties
            import subprocess
            cmd=['powershell',
                 '-Command',
                 f'(Get-CimInstance Win32_Process -Filter "ProcessID={self.pid}").CommandLine'] # noqa: E501 # pylint: disable = line-too-long
            po=subprocess.Popen(cmd,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            out,_=po.communicate()
            return out.decode('utf-8',errors='ignore').strip()
        return ''
    @property
    def commandLine(self)->"CommandLine":
        """
        Get the command line
        """
        from k_runner.cmdline import CommandLine
        return CommandLine(self.commandLineString)
    @property
    def commandline(self)->"CommandLine":
        """
        Get the command line
        """
        return self.commandLine
    @property
    def cmdline(self)->"CommandLine": # type: ignore # pylint: disable=invalid-overridden-method,line-too-long # noqa: E501
        """
        Get the command line.

        NOTE: this is a getter not a function
        making it incompatible with psutil.Process
        """
        return self.commandLine

    @property
    def modules(self)->typing.Iterable[str]:
        """
        Get all the module filenames (dll,exe,etc)
        """
        # use powershell
        # see also:
        # https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.process?view=net-5.0#properties
        import subprocess
        cmd=['powershell',
            '-Command',
            f'(Get-Process -ID {self.pid}).Modules.FileName']
        po=subprocess.Popen(cmd,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        for line in out.decode('utf-8',errors="ignore").split('\n'):
            line=line.strip()
            yield line

    @property
    def dlls(self)->typing.Iterable[str]:
        """
        Get all the dlls used by the program
        """
        for m in self.modules:
            if m.endswith('.dll'):
                yield m

    def __int__(self)->int:
        return self._pid

    @property
    def programDebugInfo(self
        )->typing.Optional[ProgramDebugInfo]: # type: ignore
        """
        Gets the registered program debug profile (in DebuggerManager)
        if there is one.
        """
        if hasDebuggerManager and self._programDebugInfo is None:
            dm=debuggerManager.DebuggerManager # type: ignore
            self._programDebugInfo=dm.getProgramDebugInfo(self.name)
        return self._programDebugInfo
    @programDebugInfo.setter
    def programDebugInfo(self,
        programDebugInfo:ProgramDebugInfo): # type: ignore
        self._programDebugInfo=programDebugInfo

    def attachDebugger(self)->str:
        """
        Attempt to attach this process to the appropriate debugger
        according to the configuation in its DebugManager profile
        """
        pdi=self.programDebugInfo
        if pdi is not None:
            return pdi.attachDebugger(self.pid) # noqa: E501 # pylint: disable=too-many-function-args
        return 'ERR: no debugger found'
    debug=attachDebugger

    def getName(self,onError:typing.Union[str,Exception,None]='')->str:
        """
        Gets the name of the process by pid

        :onError: can be Exception, None, or name of string to return

        NOTE: Should work on any os
        """
        if self._name is None:
            if os.name=='nt':
                try:
                    handle=win32api.OpenProcess(
                        win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ, # noqa: E501
                        False,self.pid)
                    self._name=win32process.GetModuleFileNameEx(handle,0)
                except pywintypes.error as e: # type: ignore # pylint: disable = no-member
                    if isinstance(onError,Exception):
                        raise e
                    self._name=onError
            else:
                self._name=super().name()
                if not self._name:
                    self._name=''
        if self._name is None:
            return ''
        return self._name
    @property
    def name(self)->str: # type: ignore # pylint: disable=invalid-overridden-method # noqa: E501
        """
        Gets the name of the process by pid
        """
        return self.getName()

    def makeForeground(self)->None:
        """
        Bring all associated windows to the top

        NOTE: Be a good citizen and use this sparingly!
        """
        for w in self.windows:
            w.makeForeground()
    bringToFront=makeForeground
    makeWindowForeground=makeForeground

    def setMinimized(self,minimize:bool=True)->None:
        """
        Minimize all windows
        """
        for w in self.windows:
            w.minimize(minimize)
    minimize=setMinimized

    def setMaximized(self,maximize:bool=True)->None:
        """
        Maximize all windows
        """
        for w in self.windows:
            w.setMaximized(maximize)
    maximize=setMaximized

    def restore(self)->None:
        """
        Restore all windows
        """
        for w in self.windows:
            w.restore()

    def priorityToNice(self,priority:float)->int:
        """
        Change a priority percent into something
        that the nice command understands.
        """
        niceVal=max(min(priority,1.0),0)
        niceVal=20-40*niceVal
        return int(niceVal)

    def niceToPriority(self,nice:float)->float:
        """
        Change a nice command value
        into a priority percent
        """
        return (nice-20)/-40

    def setPriority(self,priority:float)->None:
        """
        Set the process priority as a percent
        where 1.0 is the max priority of 100%
        """
        self.nice(self.priorityToNice(priority))

    def getPriority(self)->float:
        """
        Get the process priority as a percent
        where 1.0 is the max priority of 100%
        """
        nice=float(self.nice()) # type: ignore
        return self.niceToPriority(nice)

    @property
    def priority(self)->float:
        """
        Get/set the process priority as a percent
        where 1.0 is the max priority of 100%
        """
        return self.getPriority()
    @priority.setter
    def priority(self,priority:float):
        """
        Get/set the process priority as a percent
        where 1.0 is the max priority of 100%
        """
        return self.setPriority(priority)

    def increasePriority(self,byAmount:float=0.475)->None:
        """
        Increase the process priority percent
        """
        self.setPriority(self.getPriority()+byAmount)

    def decreasePriority(self,byAmount:float=0.475)->None:
        """
        Decrease the process priority percent
        """
        self.increasePriority(-byAmount)

    def getHwnds(self,visibleOnly:bool=True)->typing.Iterable[int]:
        """
        Get the window handles associated with the process
        """
        from .find import getHwndsByPid
        return getHwndsByPid(self.pid,visibleOnly)

    @property
    def hwnds(self)->typing.Iterable[int]:
        """
        Get the window handles associated with the process
        """
        return self.getHwnds()

    @property
    def hwnd(self)->typing.Optional[int]:
        """
        Get the primary window handle associated with the process
        """
        for hwnd in self.hwnds:
            return hwnd
        return None

    def __eq__(self,
        other:typing.Union[str,ProcessCompatible]
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
        return Process(other).pid==self.pid

    @property
    def pid(self)->int:
        """
        The pid number of the process
        """
        return self._pid

    def __repr__(self):
        return '[0x%08x] %s'%(self.pid,self.commandline)

    def cmdlineMatches(self,
        other:typing.Union[
            str,Path,typing.Pattern[str],typing.Iterable[str],"Process"]
        )->bool:
        """
        Test if the command line for this process matches a given
        executable name, regex, or all commandline parameters
        """
        exe=Path(os.path.expandvars(str(self.exe))).absolute()
        if hasattr(other,'match'):
            other=typing.cast(typing.Pattern[str],other)
            m=other.match(exe) # type: ignore
            return m is not None
        if isinstance(other,Process):
            other=str(other.cmdline)
        if isinstance(other,(str,Path)):
            if isinstance(other,str):
                other=Path(os.path.expandvars(other)).absolute()
            return exe==other
        isSame=True
        other=typing.cast(typing.Iterable[str],other)
        ourCmd=typing.cast(typing.Iterable[str],self.cmdline)
        for e1,e2 in other,ourCmd:
            if e1!=e2:
                isSame=False
                break
        return isSame

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

    def getWindows(self)->typing.Iterable["Window"]:
        """
        Get all top level windows for the process
        """
        return [Window(hWnd) for hWnd in self.hWnds]
    @property
    def windows(self)->typing.Iterable["Window"]:
        """
        Get all top level windows for the process
        """
        return self.getWindows()

    def getWindow(self)->typing.Optional["Window"]:
        """
        Get the main top level windows for the process
        """
        hWnd=self.hWnd
        if hWnd is None:
            return None
        return Window(hWnd)
    @property
    def window(self)->typing.Optional["Window"]:
        """
        Get all top level windows for the process
        """
        return self.getWindow()

    def getProcessHwnds(self)->typing.Iterable[int]:
        """
        Get all top-level windows associated with
        the process being debugged
        """
        from .find import pidToHwnds
        return pidToHwnds(self.pid)
    @property
    def hWnds(self)->typing.Iterable[int]:
        """
        Get all top-level windows associated with
        the process being debugged
        """
        return self.getProcessHwnds()

    def getProcessHwnd(self)->int:
        """
        Get main top-level window associated with
        the process being debugged

        Can throw IndexError if there is no window.
        """
        from .find import pidToHwnd
        return pidToHwnd(self.pid)
    @property
    def hWnd(self)->int:
        """
        Get the main top-level window associated with
        the process being debugged

        Can throw IndexError if there is no window.
        """
        return self.getProcessHwnd()

    def __hash__(self)->int:
        return self.pid
