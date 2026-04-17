"""
Tool for manipulation system processes.

You can either create a ProcessManipulator and
do as you will with it, or derive from ProcessManipulator
with a member called pid, that the manipulator will operate on.
"""
import typing
import os
import datetime
from pathlib import Path
import psutil
if os.name=='nt':
    import win32api # type: ignore # pylint: disable=import-error
    import win32process # type: ignore # pylint: disable=import-error
    import win32con # type: ignore # pylint: disable=import-error
    import pywintypes # type: ignore # pylint: disable=import-error
try:
    import codeTools.debuggerManager as debuggerManager # type: ignore
    from codeTools import ProgramDebugInfo # type: ignore
    hasDebuggerManager=True
except ImportError:
    ProgramDebugInfo=typing.Any
    hasDebuggerManager=False
from k_runner import EnvironmentVariables # pylint: disable=wrong-import-position # noqa: E501
from .asProcess import ProcessCompatible # noqa: E402,E501 # pylint: disable=wrong-import-position,line-too-long
from .exceptions import ProcessNotSpecifiedException # pylint: disable=wrong-import-position # noqa: E501
from .processStats import ProcessStats # pylint: disable=wrong-import-position
if typing.TYPE_CHECKING:
    from k_runner.ui.window import Window
    from k_runner.ui.windowHandleType import WindowHandleType
    from cmdline.commandLine import CommandLine


class Process:
    """
    Tool for manipulation system processes.

    You can either create a Process and
    do as you will with it, or derive from Process
    with a member called pid, that the process will operate on.

    TODO: I feel like I want to have the pid be more dynamic
    like it is pulled from the variable every time it is needed.
    Only time and testing will tell whether this is suitable as-is.

    This is compatible with psutil.Process except:
        * cmdline is a CommandLine object
        * name is not a function call, but a property
        * cwd is a Path property
        * environ is EnvironmentVariables object
        * children/parent processes are Process properties
        * numerous aliases to make using this more intuitive
    """
    def __init__(self,pid:typing.Optional[ProcessCompatible]):
        if pid is not None:
            while not isinstance(pid,int):
                if hasattr(pid,'process'):
                    pid=typing.cast(
                        ProcessCompatible,pid.process) # type: ignore
                if hasattr(pid,'pid'):
                    pid=typing.cast(ProcessCompatible,pid.pid) # type: ignore
        self._pid:typing.Optional[int]=pid
        self._psutilProcess=psutil.Process(pid)
        self._name:typing.Optional[str]=None
        self._programDebugInfo:typing.Optional[typing.Any]=None
        self.as_dict=self._psutilProcess.as_dict # type: ignore
        self.connections=self._psutilProcess.connections # type: ignore
        self.cpu_affinity=self._psutilProcess.cpu_affinity
        self.cpuAffinity=self._psutilProcess.cpu_affinity
        if hasattr(self._psutilProcess,'cpu_num'):
            self.cpu_num=self._psutilProcess.cpu_num # type: ignore
            self.cpuNum=self._psutilProcess.cpu_num # type: ignore
        self.cpu_percent=self._psutilProcess.cpu_percent
        self.cpuPercent=self._psutilProcess.cpu_percent
        self.cpu_times=self._psutilProcess.cpu_times
        self.cpuTimes=self._psutilProcess.cpu_times
        self.create_time=self._psutilProcess.create_time
        self.exe=self._psutilProcess.exe
        if hasattr(self._psutilProcess,'gids'):
            self.gids=self._psutilProcess.gids # type: ignore
        self.io_counters=self._psutilProcess.io_counters
        self.ionice=self._psutilProcess.ionice
        self.is_running=self._psutilProcess.is_running
        self.memory_full_info=self._psutilProcess.memory_full_info
        self.memory_info=self._psutilProcess.memory_info
        if hasattr(self._psutilProcess,'memory_info_ex'):
            self.memory_info_ex=self._psutilProcess.memory_info_ex # type: ignore # noqa: E501
        self.memory_maps=self._psutilProcess.memory_maps # type: ignore
        self.memory_percent=self._psutilProcess.memory_percent
        self.num_ctx_switches=self._psutilProcess.num_ctx_switches
        if hasattr(self._psutilProcess,'num_fds'):
            self.num_fds=self._psutilProcess.num_fds # type: ignore
        self.num_handles=self._psutilProcess.num_handles
        self.num_threads=self._psutilProcess.num_threads
        self.oneshot=self._psutilProcess.oneshot
        self.open_files=self._psutilProcess.open_files
        self.resume=self._psutilProcess.resume
        if hasattr(self._psutilProcess,'rlimit'):
            self.rlimit=self._psutilProcess.rlimit # type: ignore
            self.resourceLimits=self._psutilProcess.rlimit # type: ignore
        self.send_signal=self._psutilProcess.send_signal
        self.signal=self._psutilProcess.send_signal
        self.status=self._psutilProcess.status
        self.suspend=self._psutilProcess.suspend
        self.pause=self._psutilProcess.suspend
        if hasattr(self._psutilProcess,'terminal'):
            self.terminal=self._psutilProcess.terminal # type: ignore
        if hasattr(self._psutilProcess,'num_fds'):
            self.num_fds=self._psutilProcess.num_fds # type: ignore
        self.terminate=self._psutilProcess.terminate
        self.threads=self._psutilProcess.threads
        if hasattr(self._psutilProcess,'uids'):
            self.uids=self._psutilProcess.uids # type: ignore
        self.username=self._psutilProcess.username

    @property
    def stats(self)->ProcessStats:
        """
        Stats for this process

        TIP: you can watch these stats for changes
        with myProcess.stats.watch(callbackFns)
        """
        return ProcessStats(self)

    @property
    def environmentVariables(self)->EnvironmentVariables:
        """
        Environment variables of the process
        """
        return EnvironmentVariables(self._psutilProcess.environ())
    @property
    def environment(self)->EnvironmentVariables:
        """
        Environment variables of the process
        """
        return self.environmentVariables
    @property
    def environ(self)->EnvironmentVariables:
        """
        Environment variables of the process
        """
        return self.environmentVariables
    @property
    def env(self)->EnvironmentVariables:
        """
        Environment variables of the process
        """
        return self.environmentVariables

    @property
    def currentWorkingDirectory(self)->Path:
        """
        Current Working Directory
        """
        cwd=self._psutilProcess.cwd()
        if cwd is None or not isinstance(cwd,str): # type: ignore
            raise ValueError(f'Working directory unexpected value {cwd}')
        return Path(cwd)
    @property
    def workingDirectory(self)->Path:
        """
        Current Working Directory
        """
        return self.currentWorkingDirectory
    @property
    def cwd(self)->Path:
        """
        Current Working Directory
        """
        return self.currentWorkingDirectory

    @property
    def executableFilename(self)->Path:
        """
        Get the filename of this executable
        """
        return Path(self._psutilProcess.exe())
    @property
    def executableFile(self)->Path:
        """
        Get the filename of this executable
        """
        return self.executableFilename
    @property
    def executable(self)->Path:
        """
        Get the filename of this executable
        """
        return self.executableFilename
    @property
    def filename(self)->Path:
        """
        Get the filename of this executable
        """
        return self.executableFilename

    def kill(self,signal:int=-9):
        """
        Make kill act a little more like linux kill command
        """
        if signal==-9:
            self._psutilProcess.kill()
        else:
            self._psutilProcess.send_signal(signal)

    @property
    def openFiles(self)->typing.Iterable[Path]:
        """
        All of the files it has open
        """
        for f,_ in self._psutilProcess.open_files():
            yield Path(f)

    @property
    def isRunning(self)->bool:
        """
        Is the process running?
        """
        return self._psutilProcess.is_running()
    @property
    def running(self)->bool:
        """
        Is the process running?
        """
        return self.isRunning
    @property
    def isStopped(self)->bool:
        """
        Is the process running?
        """
        return not self.isRunning
    @property
    def stopped(self)->bool:
        """
        Is the process running?
        """
        return not self.isRunning

    @property
    def startTime(self)->datetime.datetime:
        """
        When was the process started
        """
        return datetime.datetime.fromtimestamp(
            self._psutilProcess.create_time())
    @property
    def started(self)->datetime.datetime:
        """
        When was the process started
        """
        return self.startTime
    @property
    def creationTime(self)->datetime.datetime:
        """
        When was the process started
        """
        return self.startTime

    @property
    def children(self)->typing.Iterable["Process"]:
        """
        All immediate child processes
        """
        for c in self._psutilProcess.children(False):
            yield Process(c)

    @property
    def descendants(self)->typing.Iterable["Process"]:
        """
        All descended child processes
        """
        for c in self._psutilProcess.children(False):
            yield Process(c)

    @property
    def parent(self)->typing.Optional["Process"]:
        """
        Parent process
        """
        ret=self._psutilProcess.parent()
        if ret is None:
            return ret
        return Process(ret)

    @property
    def parents(self)->typing.Iterable["Process"]:
        """
        All parent processes
        """
        for p in self._psutilProcess.parents():
            yield Process(p)

    @property
    def psutilProcess(self)->psutil.Process:
        """
        Get as a psutil.Process object
        """
        return self._psutilProcess

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
            c:typing.Any=wmi.WMI() # type: ignore
            print(dir(c)) # type: ignore
            #raise Exception()
            for process in c.Win32_Process(): # type: ignore
                print(process.CommandLine) # type: ignore
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
    def cmdline(self)->"CommandLine":
        """
        Get the command line.

        NOTE: this is a getter not a function
        making it incompatible with psutil.Process
        """
        return self.commandLine
    @property
    def argv(self)->typing.List[str]:
        """
        sys argv value
        """
        return self.commandLine
    @property
    def argc(self)->int:
        """
        sys argc value
        (count of command line arguments including application name)
        """
        return len(self.commandLine)
    @property
    def args(self)->typing.List[str]:
        """
        command line arguments excluding the application name
        """
        return self.commandLine[1:]

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
        return self.pid

    @property
    def programDebugInfo(self # type: ignore
        )->typing.Optional[ProgramDebugInfo]: # type: ignore
        """
        Gets the registered program debug profile (in DebuggerManager)
        if there is one.
        """
        if hasDebuggerManager and self._programDebugInfo is None:
            dm=debuggerManager.DebuggerManager # type: ignore
            self._programDebugInfo=\
                dm.getProgramDebugInfo(self.name) # type: ignore
        return self._programDebugInfo # type: ignore
    @programDebugInfo.setter
    def programDebugInfo(self,
        programDebugInfo:ProgramDebugInfo): # type: ignore
        self._programDebugInfo=programDebugInfo

    def attachDebugger(self)->str:
        """
        Attempt to attach this process to the appropriate debugger
        according to the configuration in its DebugManager profile
        """
        pdi=self.programDebugInfo # type: ignore
        if pdi is not None:
            return pdi.attachDebugger(self.pid)  # type: ignore # noqa: E501 # pylint: disable=too-many-function-args
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
                    self._name=str(
                        win32process.GetModuleFileNameEx( # type: ignore
                            handle,0))
                except pywintypes.error as e: # type: ignore # pylint: disable=no-member # noqa: E501
                    if isinstance(onError,Exception):
                        raise e
            else:
                self._name=self._psutilProcess.name()
                if not self._name:
                    self._name=''
        if self._name is None:
            self._name='[UNKNOWN]'
        if self._name is None: # type: ignore
            return ''
        return self._name
    @property
    def name(self)->str:
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

    def nice(self,niceness:typing.Optional[int]=None)->int:
        """
        Linux nice utility
        """
        return self._psutilProcess.nice(niceness) # type: ignore

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
    def hwnds(self)->typing.Iterable["WindowHandleType"]:
        """
        Get the window handles associated with the process
        """
        return self.getHwnds()

    @property
    def hwnd(self)->typing.Optional["WindowHandleType"]:
        """
        Get the primary window handle associated with the process
        """
        for hwnd in self.hwnds:
            return hwnd
        return None

    def __eq__(self, # type: ignore
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
        if self._pid is None:
            raise ProcessNotSpecifiedException()
        return self._pid

    def __repr__(self):
        return '[0x%08x] %s'%(self.pid,self.commandline)

    @property
    def shortName(self)->str:
        """
        Name without the filename decoration stuff
        """
        return Path(self.name).stem

    def processNameMatches(self,
        other:typing.Union[
            str,typing.Pattern[str],"Process"]
        )->bool:
        """
        Test if the process name for this process matches a given
        executable name, or regex
        """
        if isinstance(other,Process):
            other=other.name
        if isinstance(other,str):
            return other.lower()==self.shortName.lower()
        return other.match(self.name) is not None

    def cmdlineMatches(self,
        other:typing.Union[
            str,Path,typing.Pattern[str],typing.Iterable[str],
            "Process","CommandLine"]
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
            try:
                return self.executableFilename==other
            except Exception:
                return False
        if hasattr(other,'match'):
            other=typing.cast(typing.Pattern[str],other)
            return other.match(str(self.executableFilename)) is not None
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
        for connInfo in self._psutilProcess.net_connections(): # type: ignore # pylint: disable=no-member
            if connInfo[2] in ('inet4','tcp4','udp4'):
                port=int(connInfo[3].rsplit(':',1)[-1]) # type: ignore
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
        from k_runner.ui.window import Window
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
        from k_runner.ui.window import Window
        return Window(hWnd)
    @property
    def window(self)->typing.Optional["Window"]:
        """
        Get all top level windows for the process
        """
        return self.getWindow()

    def getProcessHwnds(self)->typing.Iterable["WindowHandleType"]:
        """
        Get all top-level windows associated with
        the process being debugged
        """
        from .find import pidToHwnds
        return pidToHwnds(self.pid)
    @property
    def hWnds(self)->typing.Iterable["WindowHandleType"]:
        """
        Get all top-level windows associated with
        the process being debugged
        """
        return self.getProcessHwnds()

    def getProcessHwnd(self)->typing.Optional["WindowHandleType"]:
        """
        Get main top-level window associated with
        the process being debugged

        Can throw IndexError if there is no window.
        """
        from .find import getHwndsByPid
        for hwnd in getHwndsByPid(self.pid):
            return hwnd
        return None
    @property
    def hWnd(self)->typing.Optional["WindowHandleType"]:
        """
        Get the main top-level window associated with
        the process being debugged

        Can throw IndexError if there is no window.
        """
        return self.getProcessHwnd()

    def __hash__(self)->int:
        return self.pid


def getCurrentProcess()->Process:
    """
    The currently running process
    """
    return Process(os.getpid())
currentProcess=getCurrentProcess
thisProcess=getCurrentProcess
