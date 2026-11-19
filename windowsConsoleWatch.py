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
import threading
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
    # a venv launcher can give this process its own console,
    # which blocks AttachConsole
    k.FreeConsole()
    # a detached target creates its console some time after launch,
    # so keep trying until it exists or the process exits
    while not k.AttachConsole(pid):
        if not proc or k.WaitForSingleObject(proc,0)==0:
            print(f'AttachConsole({pid}) failed, '
                f'error {ctypes.get_last_error()}',file=sys.stderr)
            return 1
        time.sleep(interval)
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
        target:typing.Union[int,typing.Union[str,typing.Iterable[str]]],
        pollingInterval:float=DEFAULT_INTERVAL):
        """
        :param target: pid of a running process, or a command line to launch
            in a new console
        :param pollingInterval: seconds between console polls
        """
        if isinstance(target,str):
            target=[target]
        elif isinstance(target,int):
            pass
        else:
            target=list(target)
        self.target=target
        self.pollingInterval=pollingInterval
        self._matchLineHandlers:typing.List[typing.Tuple[
            typing.Pattern[str],ConsoleOutputCallback]]=[]
        self._allLineHandlers:typing.List[ConsoleOutputCallback]=[]
        self._stdoutLineHandlers:typing.List[typing.Callable[[str],None]]=[]
        self._handlerLock=threading.Lock()
        self._pumpThreads:typing.List[threading.Thread]=[]
        self.targetProcess:typing.Optional[subprocess.Popen[str]]=None
        self._helperProcess:typing.Optional[subprocess.Popen[str]]=None

    def poll(self)->typing.Optional[int]:
        """
        Poll the target process for its exit code.

        :return: exit code if the process has terminated, None otherwise
        """
        if self.targetProcess is None:
            return None
        return self.targetProcess.poll()

    def wait(self)->typing.Optional[int]:
        """
        Wait for the target process to terminate and return its exit code.

        :return: exit code of the target process, or None if not started
        """
        code=None
        if self.targetProcess is not None:
            code=self.targetProcess.wait()
        self.join()
        return code

    def join(self)->None:
        """
        Wait until all output from the target has been dispatched
        """
        for thread in self._pumpThreads:
            thread.join()

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
        if isinstance(pattern,str):
            pattern=re.compile(pattern)
        self._matchLineHandlers.append((pattern,callback))
    add=register
    append=register

    def registerStdout(self,callback:typing.Callable[[str],None])->None:
        """
        Call callback(line) for every line the launched target writes to its
        redirected stdout/stderr (as opposed to its console screen buffer).
        Only applies when the target is launched by this watcher.
        Registering one redirects the target's stdout to a pipe, which
        can leave its console window empty; register before start().
        """
        self._stdoutLineHandlers.append(callback)

    def _handleLine(self,line:str)->None:
        """
        Send one line to every interested callback
        """
        with self._handlerLock:
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

    def _pump(self,
        stream:typing.IO[str],
        handler:typing.Callable[[str],None])->None:
        """
        Thread body: feed each line from stream to handler until EOF
        """
        for raw in stream:
            handler(raw.rstrip('\r\n'))

    def _handleStdoutLine(self,line:str)->None:
        """
        Send one target stdout line to the stdout callbacks
        """
        with self._handlerLock:
            for callback in self._stdoutLineHandlers:
                callback(line)

    def start(self)->int:
        """
        Launch the target if needed and start the helper process

        :return: pid being watched
        """
        if isinstance(self.target,int):
            pid=self.target
        else:
            capture=bool(self._stdoutLineHandlers)
            self.targetProcess=subprocess.Popen(self.target,
                creationflags=CREATE_NEW_CONSOLE,
                stdout=subprocess.PIPE if capture else None,
                stderr=subprocess.STDOUT if capture else None,
                encoding="utf-8",errors="replace")
            pid=self.targetProcess.pid
        cmd=[
            sys.executable,
            os.path.abspath(__file__),
            f'--reader={pid}',
            f'--interval={self.pollingInterval}',
            '--all']
        self._helperProcess=subprocess.Popen(
            cmd,stdout=subprocess.PIPE,stdin=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS,encoding="utf-8",errors="replace")
        streams:typing.List[typing.Tuple[
            typing.Optional[typing.IO[str]],typing.Callable[[str],None]]]=[
            (self._helperProcess.stdout,self._handleLine),
            (self.targetProcess.stdout if self.targetProcess else None,
                self._handleStdoutLine)]
        for stream,handler in streams:
            if stream is not None:
                thread=threading.Thread(
                    target=self._pump,args=(stream,handler),daemon=True)
                thread.start()
                self._pumpThreads.append(thread)
        return pid

    def run(self)->None:
        """
        Dispatch output until the watched process exits or Ctrl-C
        """
        self.start()
        try:
            self.join()
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


if typing.TYPE_CHECKING:
    from .osRunJob import OsRunJob
    from .osrun import OsRun
class ConsoleWatcherPlus(ConsoleWatcher):
    """
    Watches everything.

    That means it monitors all of the following:
        the program's stdout and stderr streams
        the program's console window output

    NOTE: a program whose stdout is redirected to a pipe writes nothing to
    its console window.  So the stdout is only redirected (and the console
    left empty) if a stdout handler is registered with registerStdout().
    """

    def __init__(self,
        target:typing.Union[int,str,typing.Iterable[str]],
        pollingInterval:float=DEFAULT_INTERVAL):
        """
        :param target: pid of a running process (console only), or a command
            line to launch with OsRun (stdout, stderr and console)
        :param pollingInterval: seconds between console polls
        """
        ConsoleWatcher.__init__(self,target,pollingInterval)
        self.runCommand:typing.Optional["OsRun"]=None
        self.targetJob:typing.Optional["OsRunJob"]=None

    def poll(self)->typing.Optional[int]:
        """
        :return: exit code if the process has terminated, None otherwise
        """
        if self.targetJob is None:
            return ConsoleWatcher.poll(self)
        if self.targetJob.isRunning:
            return None
        result=self.targetJob.result
        return None if result is None else result.returncode

    def wait(self)->typing.Optional[int]:
        """
        Wait for the target to terminate and all its output to be dispatched

        :return: exit code of the target process, or None if not launched
        """
        if self.targetJob is None:
            return ConsoleWatcher.wait(self)
        code=self.targetJob.wait().returncode
        self.join()
        return code

    def start(self)->int:
        """
        Launch the target if needed and start watching it

        :return: pid being watched
        """
        if isinstance(self.target,int) or not self._stdoutLineHandlers:
            return ConsoleWatcher.start(self)
        from .osrun import OsRun
        # detached: the target has no console to inherit, so it creates
        # its own window while OsRun still captures stdout and stderr
        self.runCommand=OsRun(self.target,detach=True)
        self.runCommand.addLineNotify(
            OsRun.STDOUT,self._handleStdoutLine)
        self.runCommand.addLineNotify(
            OsRun.STDERR,self._handleStdoutLine)
        self.targetJob=self.runCommand.runAsync() # type: ignore
        self.targetProcess=self.targetJob # type: ignore
        if self.targetJob is None:
            raise RuntimeError("Failed to start target job")
        pid=self.targetJob.pid
        # run as a module because this file has package-relative imports
        packageParent=os.path.dirname(os.path.abspath(__file__))
        cmd=[
            sys.executable,
            '-m',__name__,
            f'--reader={pid}',
            f'--interval={self.pollingInterval}']
        self._helperProcess=subprocess.Popen(
            cmd,stdout=subprocess.PIPE,stdin=subprocess.DEVNULL,
            cwd=packageParent,
            creationflags=DETACHED_PROCESS,encoding="utf-8",errors="replace")
        if self._helperProcess.stdout is not None:
            thread=threading.Thread(target=self._pump,
                args=(self._helperProcess.stdout,self._handleLine),
                daemon=True)
            thread.start()
            self._pumpThreads.append(thread)
        return pid


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
    plus=False
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
            elif av[0]=='--plus':
                plus=True
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
    if plus:
        watcher=ConsoleWatcherPlus(
            pid if pid is not None else command,interval)
    else:
        watcher=ConsoleWatcher(
            pid if pid is not None else command,interval)
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
