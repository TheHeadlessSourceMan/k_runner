"""
Watch the debug console of a windows process in real time

Some windows programs open their own Windows console and write to
that console's screen buffer (not stdout, and not OutputDebugString),
so redirecting stdout captures nothing.

Instead, we use a helper process with no console of its
own to attach to the target's console, poll the screen buffer for new lines,
and stream them through a pipe to ConsoleWatcher, which dispatches each
line to the callbacks registered for any pattern it matches.
"""
import ctypes
import os
import re
import subprocess
import sys
import time
import typing
from ctypes import wintypes


# rows re-read per poll; more scrolling than this between polls loses lines
TAIL_ROWS:int=400
DEFAULT_INTERVAL:float=0.05

SYNCHRONIZE:int=0x00100000
GENERIC_RW:int=0xC0000000
SHARE_RW:int=3
OPEN_EXISTING:int=3
DETACHED_PROCESS:int=0x00000008
CREATE_NEW_CONSOLE:int=0x00000010

ConsoleOutputCallback=typing.Union[
    typing.Callable[[str,typing.Optional[typing.Match[str]]],None],
    typing.Callable[[str],None]]


class COORD(ctypes.Structure):
    """
    Win32 COORD
    """
    _fields_=[("X",wintypes.SHORT),("Y",wintypes.SHORT)]


class SMALL_RECT(ctypes.Structure):
    """
    Win32 SMALL_RECT
    """
    _fields_=[(n,wintypes.SHORT) for n in ("Left","Top","Right","Bottom")]


class CSBI(ctypes.Structure):
    """
    Win32 CONSOLE_SCREEN_BUFFER_INFO
    """
    _fields_=[
        ("dwSize",COORD),
        ("dwCursorPosition",COORD),
        ("wAttributes",wintypes.WORD),
        ("srWindow",SMALL_RECT),
        ("dwMaximumWindowSize",COORD),
        ]


def _kernel32()->ctypes.WinDLL:
    """
    Get kernel32 with the argument types we use declared
    """
    k=ctypes.WinDLL("kernel32",use_last_error=True)
    k.CreateFileW.restype=wintypes.HANDLE
    k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
        wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    k.OpenProcess.restype=wintypes.HANDLE
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    k.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    k.GetConsoleScreenBufferInfo.argtypes=[
        wintypes.HANDLE,ctypes.POINTER(CSBI)]
    k.ReadConsoleOutputCharacterW.argtypes=[wintypes.HANDLE,wintypes.LPWSTR,
        wintypes.DWORD,COORD,ctypes.POINTER(wintypes.DWORD)]
    k.AttachConsole.argtypes=[wintypes.DWORD]
    return k


def readConsole(pid:int,interval:float=DEFAULT_INTERVAL)->int:
    """
    Helper process body: attach to the console of pid and write each new
    complete line to stdout until the process exits

    :return: process exit code
    """
    k=_kernel32()
    proc=k.OpenProcess(SYNCHRONIZE,False,pid)
    if not k.AttachConsole(pid):
        print(f'AttachConsole({pid}) failed, error {ctypes.get_last_error()}',
            file=sys.stderr)
        return 1
    con=k.CreateFileW("CONOUT$",GENERIC_RW,SHARE_RW,None,OPEN_EXISTING,0,None)
    prev:typing.Optional[typing.List[str]]=None
    while True:
        alive=bool(proc) and k.WaitForSingleObject(proc,0)!=0
        info=CSBI()
        if not k.GetConsoleScreenBufferInfo(con,ctypes.byref(info)):
            break
        width=info.dwSize.X
        # the cursor row holds a partial line, unless the process has exited
        end=info.dwCursorPosition.Y+(0 if alive else 1)
        start=max(0,end-TAIL_ROWS)
        buf=ctypes.create_unicode_buffer(width)
        count=wintypes.DWORD()
        cur:typing.List[str]=[]
        for row in range(start,end):
            k.ReadConsoleOutputCharacterW(
                con,buf,width,COORD(0,row),ctypes.byref(count))
            cur.append(buf.value.rstrip())
        new=cur
        if prev is not None:
            # find how far the console scrolled:
            #   smallest shift where old tail matches new head
            for shift in range(len(prev)+1):
                tail=prev[shift:]
                if cur[:len(tail)]==tail:
                    new=cur[len(tail):]
                    break
        for line in new:
            sys.stdout.write(line+'\n')
        sys.stdout.flush()
        prev=cur
        if not alive:
            break
        time.sleep(interval)
    return 0


class ConsoleWatcher:
    """
    Watches the console of a process and calls back on lines matching patterns

    Example:
        watcher=ConsoleWatcher(['target_program.exe'])
        watcher.register(r'ERROR',lambda line,m:print(line))
        watcher.run()
    """

    def __init__(self,
        target:typing.Union[int,typing.Sequence[str]],
        pollingInterval:float=DEFAULT_INTERVAL):
        """
        :param target: pid of a running process, or a command line to launch
            in a new console
        :param pollingInterval: seconds between console polls
        """
        self.target=target
        self.pollingInterval=pollingInterval
        self._matchLineHandlers:typing.List[typing.Tuple[
            typing.Pattern[str],ConsoleOutputCallback]]=[]
        self._allLineHandlers:typing.List[ConsoleOutputCallback]=[]
        self.targetProcess:typing.Optional[subprocess.Popen[bytes]]=None
        self._helperProcess:typing.Optional[subprocess.Popen[str]]=None

    def register(self,
        callback:ConsoleOutputCallback,
        pattern:typing.Union[None,str,typing.Pattern[str]]=None
        )->None:
        """
        Call callback(line,match) for every line where pattern is found
        """
        if pattern is None:
            self._allLineHandlers.append(callback)
            return
        self._allLineHandlers.append(callback)
        if isinstance(pattern,str):
            pattern=re.compile(pattern)
        self._matchLineHandlers.append((pattern,callback))
    add=register
    append=register

    def _handleLine(self,line:str)->None:
        """
        Send one line to every interested callback
        """
        for lineHandler in self._allLineHandlers:
            if lineHandler.__code__.co_argcount==2:
                lineHandler(line,None) # type: ignore
            else:
                lineHandler(line) # type: ignore
        for pattern,callback in self._matchLineHandlers:
            match=pattern.search(line)
            if match:
                if callback.__code__.co_argcount==1:
                    callback(line) # type: ignore
                else:
                    callback(line,match) # type: ignore

    def start(self)->int:
        """
        Launch the target if needed and start the helper process

        :return: pid being watched
        """
        if isinstance(self.target,int):
            pid=self.target
        else:
            self.targetProcess=subprocess.Popen(
                list(self.target),creationflags=CREATE_NEW_CONSOLE)
            pid=self.targetProcess.pid
        cmd=[
            sys.executable,os.path.abspath(__file__),
            f'--reader={pid}',
            f'--interval={self.pollingInterval}']
        self._helperProcess=subprocess.Popen(
            cmd,stdout=subprocess.PIPE,stdin=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS,encoding="utf-8",errors="replace")
        return pid

    def run(self)->None:
        """
        Dispatch console lines until the watched process exits or Ctrl-C
        """
        self.start()
        if self._helperProcess is None or self._helperProcess.stdout is None:
            return
        try:
            for raw in self._helperProcess.stdout:
                self._handleLine(raw.rstrip('\n'))
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self)->None:
        """
        Stop the helper process (the watched process is left running)
        """
        if self._helperProcess is not None \
            and self._helperProcess.poll() is None:
            # Terminate the helper process if it is still running
            self._helperProcess.terminate()


def cmdline(args:typing.Sequence[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    pid:typing.Optional[int]=None
    readPid:typing.Optional[int]=None
    interval=DEFAULT_INTERVAL
    showAll=False
    logName=''
    patterns:typing.List[str]=[]
    command:typing.List[str]=[]
    for i,arg in enumerate(args):
        if arg=='--':
            command=list(args[i+1:])
            break
        if arg.startswith('-'):
            av=[a.strip() for a in arg.split('=',1)]
            av[0]=av[0].lower()
            if av[0] in ['-h','--help']:
                printhelp=True
            elif av[0]=='--reader' and len(av)>1:
                readPid=int(av[1])
            elif av[0]=='--pid' and len(av)>1:
                pid=int(av[1])
            elif av[0]=='--interval' and len(av)>1:
                interval=float(av[1])
            elif av[0] in ['-p','--pattern'] and len(av)>1:
                patterns.append(av[1])
            elif av[0]=='--log' and len(av)>1:
                logName=av[1]
            elif av[0]=='--all':
                showAll=True
            else:
                print('ERR: unknown argument "'+arg+'"')
                printhelp=True
        else:
            print('ERR: unknown argument "'+arg+'"')
            printhelp=True
    if readPid is not None:
        return readConsole(readPid,interval)
    if printhelp or (pid is None and not command):
        print('Usage:')
        print('  windowsConsoleWatch.py [options] [--pid=num | -- command ...]') # noqa: E501
        print('Options:')
        print('   -p=regex, --pattern=regex ... print lines matching regex (repeatable)') # noqa: E501 # pylint: disable=line-too-long
        print('   --all ....................... also print non-matching lines') # noqa: E501
        print('   --log=file .................. append every captured line to file') # noqa: E501
        print(f'   --interval=seconds .......... poll interval, default={DEFAULT_INTERVAL}') # noqa: E501 # pylint: disable=line-too-long
        return -1
    watcher=ConsoleWatcher(pid if pid is not None else command,interval)
    if logName:
        log=open(logName,'a',encoding='utf-8')
    else:
        log=None
    def onMatch(line:str,m:typing.Optional[re.Match[str]]):
        """
        Callback writes to either console or log file
        depending on the presence of the log object.
        """
        if log is not None:
            log.write(line+'\n')
        elif m is not None:
            print(f'[MATCH {m.re.pattern!r}] groups={m.groups()} :: {line}',
                flush=True)
        else:
            print(f'[MATCH .*] :: {line}', flush=True)
    for pat in patterns:
        watcher.register(onMatch,pat)
    if showAll:
        watcher.register(onMatch)
    watcher.run()
    if log is not None:
        log.close()
    return 0


if __name__=='__main__':
    sys.exit(cmdline(sys.argv[1:]))
