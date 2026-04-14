"""
kRunnerTools for linux OSes
"""
import typing
import os
import time
import subprocess
import threading
import signal
try:
    import pyev # type: ignore # noqa: F401,E501 # pylint: disable=import-error,unused-import,line-too-long
    hasPyEv=True
except ImportError:
    hasPyEv=False
from .dataRecievedCallbacks import ApplicationCallbacks
from .settings import useDaemonThreads


def hideAllWindows(pid:int,hide:bool=True)->None:
    """
    Hide (or show) all windows belonging to a certain process
    """
    raise NotImplementedError()


def killProcess(pid:int)->None:
    """
    End a process.  Starts out requesting a friendly shutdown but gradually
    gets more violent.
    """
    # give it a chance to go down peacefully
    os.kill(pid,signal.SIGTERM)
    for _ in range(100):
        if not processExists(pid):
            return
        time.sleep(0.010)
    # nuke that sob!
    os.kill(pid,-9)


def processExists(pid:int)->bool:
    """
    Determine if a process exists.

    TODO:
    """
    _=pid
    raise NotImplementedError()


class Application:
    """
    Wrapper class for a running application.
    """

    def __init__(self,
        runInShell:typing.Optional[bool]=True,
        runInShellCommandFlag:str='-c'):
        """
        If runInShell=True,then use the default shell.  If it is a string,
        use the default shell.
        """
        if not runInShell:
            runInShell=None
        self.runInShell=runInShell
        self.runInShellCommandFlag=runInShellCommandFlag
        self.returnCode=None
        self.callbacks:typing.Optional[ApplicationCallbacks]=None
        # watchdog management
        self.wDogTouch=False
        self.onOutputCB:typing.Optional[typing.Callable]=None
        self.onErrorCB:typing.Optional[typing.Callable]=None
        self.dDogOutput=None
        self.wDogLifetime=None
        self.hideWindows=False
        self.wDogOutput=None
        self.returncode=None
        self.process=None
        self._imgData=None
        self._threadsKeepGoing=False
        self.granularity=0.010
        self.lifetimeCounter=0.0
        self.outputCounter=0.0
        self.wDogExitCode=-1077

    def sendIn(self,data:str,encoding:str='utf-8')->None:
        """
        Send something to the program's standard input
        """
        if self.process is None or self.process.stdin is None:
            raise Exception("Process not started")
        self.process.stdin.write(data.encode(encoding,errors="ignore"))

    def getShell(self)->str:
        """
        This returns the current shell command
        (regardless of whether or not it would be used)
        """
        if self.runInShell is None or self.runInShell:
            outBytes,errBytes=subprocess.Popen(
                'echo $SHELL',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True).communicate()
            out=outBytes.decode("utf-8",errors="ignore")
            err=errBytes.decode("utf-8",errors="ignore")
            if err:
                out='/bin/sh'
                print(('ERR: Cannot find shell.  Defaulting to '+out+'.'))
                print(('\t'+'\t\n'.join(err.split('\n'))))
            return out.strip()
        return str(self.runInShell)

    def run(self,
        cmd:typing.Union[str,typing.Iterable[str]],
        callbacks:typing.Optional[ApplicationCallbacks]=None,
        hideWindows:bool=False,
        priorityBoost:int=0,
        wDogOutput=None,
        wDogLifetime=None
        )->int:
        """
        runs a program (via the standard POSIX API)
        """
        if callbacks is None:
            callbacks=ApplicationCallbacks()
        if isinstance(cmd,str):
            cmd=[cmd]
        else:
            cmd=list(cmd)
        if self.runInShell is not None:
            cmd.insert(0,self.runInShellCommandFlag)
            cmd.insert(0,self.getShell())
        def onOutput(msg):
            """
            stdout callback
            """
            print(f'>>> {msg}')
        callbacks.addCallOnStdoutLine(onOutput)
        def onError(msg:str):
            """
            stderr callback
            """
            print("[ERR] {err}")
            # make sure we get all the error message then quit
            app.wDogOutput=None
            app.lifetimeCounter=0.0
            app.wDogLifetime=0.100
        callbacks.addCallOnStderrLine(onError)
        self.callbacks=callbacks
        self.dDogOutput=wDogOutput
        self.wDogLifetime=wDogLifetime
        self.hideWindows=hideWindows
        self.wDogOutput=wDogOutput
        result:typing.Optional[int]=0
        try:
            # TODO: This currently does not allow parameters!
            # *unless* you enable
            # shell=true,which causes un-killability problems
            self.process=subprocess.Popen(
                cmd,
                bufsize=1,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # Uncommenting the next parameter can solve some running
                # problems, but you'll no longer be able to kill the process.
                # (Personally, it's just not worth it!)
                #shell=True
                )
        except OSError as e:
            print(f'ERR: Unable to execute "{cmd}" because:')
            print(('\t',e))
            return -1
        # TODO: This next line is incorrect.  os.nice can only change
        # the current process,not an arbitrary pid
        #os.nice(self.process.pid,priorityBoost)
        # The watchdog
        t=threading.Thread(target=self._wDogThread,daemon=useDaemonThreads)
        t.start()
        # The stdout loop
        t=threading.Thread(target=self._stdoutReadThread,daemon=useDaemonThreads)
        t.start()
        # The stderr loop
        result=None
        while result is None \
            and self.returnCode is None \
            and self.process.stderr is not None:
            line=self.process.stderr.readline()
            if line is not None:
                setattr(self.process,'wDogTouch',True)
                while line and (line[-1]=='\n' or line[-1]=='\r'):
                    line=line[0:-1]
                    onErrorCB(f'{self.name}:{line}')
            result=self.process.poll()
        if self.returnCode is None:
            self.returnCode=result
        if self.returnCode is None:
            return -9999
        return self.returnCode

    def _stdoutReadThread(self):
        """
        Thread to read stdout of a (POSIX) process
        """
        result=None
        while result is None \
            and self.returnCode is None \
            and self.process is not None \
            and self.process.stdout is not None:
            #
            line=self.process.stdout.readline()
            if line is not None:
                self.wDogTouch=True
                while line and (line[-1]=='\n' or line[-1]=='\r'):
                    line=line[0:-1]
                    if self.onOutputCB is not None:
                        _=self.onOutputCB(self,line)
            result=self.process.poll()

    def _wDogThread(self):
        """
        Thread to monitor a (POSIX) process for lockups
        """
        while self.process is not None \
            and self.process.poll() is None \
            and self.returnCode is None:
            #
            if self.hideWindows:
                # Sadly,we can't specify window visibility on startup (yet).
                # We'll just have to watch for new windows
                # and hide them manually.
                hideAllWindows(self.process.pid)
            if self.wDogTouch:
                self.wDogTouch=False
                self.outputCounter=0.0
            if self.wDogOutput is not None \
                and self.outputCounter>self.wDogOutput:
                #
                killProcess(self.process.pid)
                print(("Watchdog output timer fired (",
                    self.outputCounter,self.wDogOutput,
                    ")"))
                self.returncode=self.wDogExitCode
                break
            if self.wDogLifetime is not None \
                and self.lifetimeCounter>self.wDogLifetime:
                #
                killProcess(self.process.pid)
                print(("Watchdog lifetime timer fired (",
                    self.lifetimeCounter,self.wDogLifetime,
                    ")"))
                self.returncode=self.wDogExitCode
                break
            self.lifetimeCounter=self.lifetimeCounter+self.granularity
            self.outputCounter=self.outputCounter+self.granularity
            time.sleep(self.granularity)
