from re import sub
from tkinter import E
import typing
import time

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    import pywintypes
    hasWindowsTools=True
except ImportError:
    hasWindowsTools=False


def getProcessName(pid:int,onError:typing.Any='')->str:
    """
    Gets the name of a process by pid

    :onError: can be Exception, None, or name of string to return

    TODO: currently works on windows only
    """
    try:
        handle=win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION|win32con.PROCESS_VM_READ,
            False,pid)
        return win32process.GetModuleFileNameEx(handle,0)
    except pywintypes.error as e:
        if onError==Exception:
            raise e
        return onError


def getHwndsByPid(pid:int,visibleOnly:bool=True)->typing.Iterable[int]:
    """
    Gets any and all top-level windows of a process by pid

    :visibleOnly: whether to exclude invisible windows (default is True)

    TODO: currently works on windows only
    """
    found:typing.List[int]=[]
    def enumWindowsCB(hwnd,pid):
        _,foundPid=win32process.GetWindowThreadProcessId(hwnd)
        if pid==foundPid \
            and (win32gui.IsWindowVisible(hwnd) \
            or not visibleOnly):
            #
            found.append(hwnd)
    win32gui.EnumWindows(enumWindowsCB,pid)
    return found


def getPidByHwnd(hwnd:int)->int:
    """
    Gets pid of a window

    TODO: currently works on windows only
    """
    _,foundPid=win32process.GetWindowThreadProcessId(hwnd)
    return foundPid


class UiComponent:
    """
    A single component on a ui.
    (Often called a "Window", but this can be misleading
    for the newcomer if it's something else like a button)
    """

    def __init__(self,hwnd:typing.Union[int,str]):
        self._hwnd=int(hwnd)
        self._process:typing.Optional['Process']
        self._pid:typing.Optional[int]
        # NOTE: process top level window has no parent
        self.parent:typing.Optional[UiComponent]=None

    @property
    def hwnd(self)->int:
        """
        Window handle for this component
        """
        return self._hwnd

    def __int__(self):
        return self._hwnd

    @property
    def path(self)->str:
        """
        Path made up of window names
        """
        tape=['']
        self._getPath(tape)
        return '/'.join(tape)
    def _getPath(self,tape:typing.List[str])->None:
        tape.append(self.name)
        if self.parent is not None:
            self.parent._getPath(tape)

    @property
    def tree(self)->str:
        """
        Printable tree of this window and all of its children
        """
        tape:typing.List[str]=[]
        self._tree(tape)
        return '\n'.join(tape)
    def _tree(self,tape:typing.List[str],indent:str=''):
        tape.append(indent+repr(self))
        for c in self.children:
            c._tree(tape,indent+'   ')

    @property
    def root(self)->'UiComponent':
        """
        The uppermost window root of this component
        """
        if self.parent is not None:
            return self.parent.root
        return self

    @property
    def children(self)->typing.Iterable['UiComponent']:
        """
        Child components of this component
        """
        raise NotImplementedError()

    @property
    def name(self)->str:
        """
        Name of this component
        """
        raise NotImplementedError()

    def click(self,
        x:int=0,y:int=0,
        button:str="left",
        count=1,
        clickSpeedSec=0.1
        )->None:
        """
        Click on this component
        """
        button=button[0].lower()
        if button=='r':
            dn=win32con.MOUSEEVENTF_RIGHTDOWN
            up=win32con.MOUSEEVENTF_RIGHTUP
        elif button=='m':
            dn=win32con.MOUSEEVENTF_MIDDLEDOWN
            up=win32con.MOUSEEVENTF_MIDDLEUP
        else: # button=='l':
            dn=win32con.MOUSEEVENTF_LEFTDOWN
            up=win32con.MOUSEEVENTF_LEFTUP
        for n in range(count):
            if n>0:
                time.sleep(clickSpeedSec)
            win32api.mouse_event(dn,x,y)
            time.sleep(clickSpeedSec)
            win32api.mouse_event(up,x,y)

    def sendKeys(self,
        keys:str,
        alt:bool=False,
        ctrl:bool=False,
        shift:bool=False,
        meta:bool=False
        )->None:
        """
        TODO: this mostly kinda works, but, for instance if your keys contain 
            things like "%^+~{}" then weirdness may happen.
            Also meta does not work.
        """
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        for c in keys:
            if c=='\r':
                continue
            if c=='\n':
                c='~'
            if shift:
                c='+'+c
            if ctrl:
                c='^'+c
            if alt:
                c='\%'+c
            shell.SendKeys(c,0)

    def minimize(self)->None:
        """
        Minimize this window
        """
        win32gui.ShowWindow(self.hwnd,win32con.SW_MINIMIZE)

    def maximize(self)->None:
        """
        Maximize this window
        """
        win32gui.ShowWindow(self.hwnd,win32con.SW_MAXIMIZE)

    def restore(self)->None:
        """
        Restore this window from minimized state
        """
        win32gui.ShowWindow(self.hwnd,win32con.SW_RESTORE)

    def close(self)->None:
        """
        Close this window
        """
        win32gui.PostMessage(self.hwnd,win32con.WM_CLOSE,0,0)

    def makeForeground(self)->None:
        """
        Bring any associated window to the top

        NOTE: Be a good citizen and use this sparingly!
        """
        win32gui.ShowWindow(self.hwnd,5)
        win32gui.SetForegroundWindow(self.hwnd)
    bringToFront=makeForeground
    makeWindowForeground=makeForeground

    @property
    def pid(self)->int:
        """
        Get the process id for this component
        """
        if self._pid is None:
            self._pid=getPidByHwnd(self._hwnd)
        return self._pid

    @property
    def process(self)->'Process':
        """
        Get the process for this component
        """
        if self._process is None:
            self._process=Process(self.pid)
        return self._process

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o,str):
            return self.hwnd==int(__o)
        elif isinstance(__o,int):
            return self.hwnd==__o
        elif hasattr(__o,'hwnds'):
            return self.hwnd in __o.hwnds # type: ignore
        elif hasattr(__o,'hwnd'):
            return self.hwnd==__o.hwnd # type: ignore
        elif hasattr(__o,'uiComponent'):
            return self==__o.uiComponent # type: ignore
        elif hasattr(__o,'window'):
            return self==__o.window # type: ignore
        return False

    def __repr__(self)->str:
        return '[0x%08x] %s'%(self.hwnd,self.name)
Window=UiComponent

ProcessCompatible=typing.Union[str,int,'Process']


class Process:
    """
    Handy handle to a process
    """

    def __init__(self,pid:ProcessCompatible):
        self._pid=int(pid)
        self._name:typing.Optional[str]=None
        self._programDebugInfo:typing.Optional[typing.Any]=None

    @property
    def commandline(self)->str:
        """
        Get the command line used to start a process
        """
        wmiStyle=False
        if wmiStyle:
            # Requires the wmi module:
            # http://timgolden.me.uk/python/wmi/index.html
            import wmi
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
    def programDebugInfo(self)->typing.Optional[typing.Any]:
        """
        Gets the registered program debug profile (in DebuggerManager)
        if there is one.
        """
        if self._programDebugInfo is None:
            import codeTools.debuggerManager as debuggerManager
            self._programDebugInfo=\
                debuggerManager.DebuggerManager.getProgramDebugInfo(self.name)
        return self._programDebugInfo
    @programDebugInfo.setter
    def programDebugInfo(self,programDebugInfo:typing.Any):
        self._programDebugInfo=programDebugInfo

    def attachDebugger(self)->str:
        """
        Attempt to attach this process to the appropriate debugger
        according to the configuation in its DebugManager profile
        """
        pdi=self.programDebugInfo
        if pdi is not None:
            return pdi.attachDebugger(self.pid)
        return 'ERR: no debugger found'
    debug=attachDebugger

    @property
    def name(self)->str:
        """
        The name of the process
        """
        if self._name is None:
            self._name=getProcessName(self._pid)
        return self._name

    def makeForeground(self)->None:
        """
        Bring all associated windows to the top

        NOTE: Be a good citizen and use this sparingly!
        """
        for w in self.windows:
            w.makeForeground()
    bringToFront=makeForeground
    makeWindowForeground=makeForeground

    def getHwnds(self,visibleOnly:bool=True)->typing.Iterable[int]:
        """
        Get the window handles associated with the process
        """
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

    def getUiComponents(self,
        visibleOnly:bool=True
        )->typing.Iterable[UiComponent]:
        """
        Get the top level windows associated with this process
        """
        return [UiComponent(hwnd) for hwnd in self.getHwnds(visibleOnly)]
    getWindows=getUiComponents

    @property
    def uiComponents(self)->typing.Iterable[UiComponent]:
        """
        Get the windows associated with the process
        """
        return self.getUiComponents()
    @property
    def windows(self)->typing.Iterable[UiComponent]:
        """
        Get the windows associated with the process
        """
        return self.getUiComponents()

    @property
    def uiComponent(self)->typing.Optional[UiComponent]:
        """
        Get the primary window associated with the process
        """
        for hwnd in self.hwnds:
            return UiComponent(hwnd)
        return None
    @property
    def window(self)->typing.Optional[UiComponent]:
        """
        Get the primary window associated with the process
        """
        for hwnd in self.hwnds:
            return UiComponent(hwnd)
        return None

    @property
    def priority(self)->int:
        """
        Get/set the process priority
        """
        raise NotImplementedError()
    @priority.setter
    def priority(self,priority:int):
        raise NotImplementedError()

    def kill(self):
        """
        Kill the process
        """
        raise NotImplementedError()

    def wait(self):
        """
        Wait for the process to complete
        """
        raise NotImplementedError()

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o,str):
            return self.pid==int(__o)
        elif isinstance(__o,int):
            return self.pid==__o
        elif hasattr(__o,'pid'):
            return self==__o.pid # type: ignore
        elif hasattr(__o,'process'):
            return self==__o.process # type: ignore
        return False

    @property
    def pid(self)->int:
        """
        The pid number of the process
        """
        return self._pid

    def __repr__(self):
        return '[0x%08x] %s'%(self.pid,self.commandline)


def findProcesses(
    programName:typing.Union[None,str,typing.Pattern]=None
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
    programName:typing.Union[None,str,typing.Pattern]=None
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
    printhelp=False
    currentProcesses:typing.List[Process]=[]
    for arg in args:
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-h','--help'):
                printhelp=True
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
                printhelp=True
        else:
            printhelp=True
    if printhelp or not didSomething:
        print('USEAGE:')
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
