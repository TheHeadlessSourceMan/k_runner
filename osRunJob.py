"""
Starts a new job running and collects the results.

This is the core implementation of the osrun subsystem.
"""
from io import BytesIO
import typing
import os
import time
from pathlib import Path
import subprocess
from threading import Thread
from .environmentVariables import EnvironmentVariablesCompatible
from .exceptions import OsRunException, ProcessNotSpecifedException
from .dataRecievedCallbacks import DataRecievedCallbacks
from .osRunResult import OsRunResult
from .dataRecievedCallbacks import RecieveDataManager
from .processes import Process,MEDIUM_PRIORITY
from .cmdline import CommandLine
from .settings import useDaemonThreads
if typing.TYPE_CHECKING:
    from osrun import OsRun


class OsRunJob(RecieveDataManager,Process):
    """
    Starts a new job running and collects the results.

    This is the core implementation of the osrun subsystem.
    """
    def __init__(self,
        osRun:"OsRun",
        runCallbacks:typing.Optional[DataRecievedCallbacks]=None):
        """ """
        RecieveDataManager.__init__(self,runCallbacks)
        self._result:typing.Optional[OsRunResult]=None
        self._running:bool=False
        self._outThread:typing.Optional[Thread]=None
        self._errThread:typing.Optional[Thread]=None
        self._popen:typing.Optional[subprocess.Popen]=None
        self._lastReturncode:int=-9999
        if osRun.workingDirectory is not None:
            # keep a copy in case they change it
            self._workingDirectory=Path(osRun.workingDirectory)
        else:
            self._workingDirectory=Path(os.curdir)
        self.osRun=osRun
        self.chunkyIO=False
        Process.__init__(self,None)

    @property
    def currentWorkingDirectory(self)->Path:
        """
        Current Working Directory
        """
        return self._workingDirectory

    @property
    def isRunning(self)->bool:
        """
        Is the process running?
        """
        return self._running

    @property
    def pid(self)->int:
        """
        returns the process id
        if not running, returns None
        """
        if self._popen is None:
            raise ProcessNotSpecifedException()
        return self._popen.pid

    def debugLog(self,txt:str)->None:
        """
        this is what gets called to log lines of debug text
        """
        print(txt)

    def write(self,*vals):
        """
        Write data to the job's stdin

        (NOTE: if you want carriage return, you
        may want to use writeln() instead)
        """
        if self._popen is not None \
            and self._popen.stdin is not None:
            #
            v=' '.join([str(v) for v in vals])
            self._popen.stdin.write(v)
            self._popen.stdin.flush()
    def writeln(self,*vals):
        """
        Write data to the job's stdin
        """
        if self._popen is not None \
            and self._popen.stdin is not None:
            #
            v=' '.join([str(v) for v in vals])
            self._popen.stdin.write(v)
            self._popen.stdin.write('\n')
            self._popen.stdin.flush()
    print=writeln

    def start(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None,
        moreEnvironmentVariables:typing.Optional[
            EnvironmentVariablesCompatible]=None)->None:
        """
        start the thing running

        :moreParams: add more parameters in addition to the ones specified
            in the constructor
            the idea is you could set up the command the way you want it,
            then run on multiple files
        :workingDirectory: override the app's working directory
        """
        if self.running:
            self.stop()
        # clear everything out
        self._running=True
        self._result=None
        RecieveDataManager.start(self)
        # set up debugging
        if not self.osRun.debug: # we don't want to debug
            self.removeLineNotify(self.STDOUTERR,self.debugLog) # remove it
        else: # print is not registered
            self.addLineNotify(self.STDOUTERR,self.debugLog) #register it
        # build up the command to be run
        if workingDirectory is None:
            if self.workingDirectory is None:
                workingDirectory=Path(os.getcwd()).absolute()
            else:
                workingDirectory=self.workingDirectory
        else:
            workingDirectory=Path(workingDirectory).absolute()
        cmd:CommandLine=CommandLine(self.osRun.cmd)
        cmd.extend(self.osRun.params)
        if moreParams is not None:
            cmd.extend(moreParams)
        environmentVariables=self.osRun.environmentVariables
        if moreEnvironmentVariables is not None:
            environmentVariables=environmentVariables.union(moreEnvironmentVariables)
        # launch the program
        creationflags=0
        if self.osRun.detach:
            DETACHED_PROCESS=0x00000008
            creationflags=DETACHED_PROCESS
        previousDirectory=None
        if workingDirectory:
            previousDirectory=os.getcwd()
            try:
                os.chdir(str(workingDirectory))
            except Exception as e:
                msg=f'Invalid working directory "{workingDirectory}"'
                raise FileNotFoundError(msg) from e
        if self.osRun.priority!=MEDIUM_PRIORITY:
            if os.name=='nt':
                # of the form:
                #     start "" /AboveNormal "C:\Windows\System32\mspaint.exe"
                # see also:
                # https://www.tenforums.com/tutorials/89548-set-cpu-process-priority-applications-windows-10-a.html
                from processes.priority import _getWindowsPriorityName
                if workingDirectory is None:
                    cmdPath=Path(cmd[0]).absolute()
                else:
                    cmdPath=workingDirectory/cmd[0]
                if not cmdPath.is_file():
                    cmdPath=Path(cmd[0])
                winPri=_getWindowsPriorityName(self.osRun.priority)
                newCmd=CommandLine(('start','',f'/{winPri}',str(cmdPath)))
                if len(cmd)>1:
                    newCmd.extend(cmd[1:])
                cmd=newCmd
                self.osRun.shell=True
            else:
                self.priority=self.osRun.priority
        if os.name=='nt':
            from win32con import SW_MINIMIZE,SW_MAXIMIZE,SW_HIDE
            startupinfo=subprocess.STARTUPINFO()
            startupinfo.dwFlags=subprocess.STARTF_USESHOWWINDOW
            if self.osRun.showMinimized:
                startupinfo.wShowWindow|=SW_MINIMIZE
            if self.osRun.showMaximized:
                startupinfo.wShowWindow|=SW_MAXIMIZE
            if self.osRun.showHidden:
                startupinfo.wShowWindow|=SW_HIDE
        else:
            startupinfo=None
        if self.osRun.debug:
            print(f'$> {cmd}')
        try:
            # NOTE: the following throws a warning message,
            # thus the workaround below.
            # see:
            #    https://bugs.python.org/issue32236
            #self._popen=subprocess.Popen(cmd,
            #    shell=self.osRun.shell,
            #    stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            #    bufsize=1,creationflags=creationflags,cwd=workingDirectory)
            self._popen=subprocess.Popen(
                cmd.encodeToArray(),
                shell=self.osRun.shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                creationflags=creationflags,
                cwd=str(workingDirectory),
                env=environmentVariables.jsonObj,
                startupinfo=startupinfo
                )
        except Exception as e:
            raise OsRunException(cmd,e) from e # type: ignore
        if self.chunkyIO:
            try:
                # If this api is available, we probably need to call it
                os.set_blocking(self._popen.stdout.fileno(),False) # type: ignore # pylint: disable=no-member # noqa: E501
                os.set_blocking(self._popen.stderr.fileno(),False) # type: ignore # pylint: disable=no-member # noqa: E501
            except Exception as e:
                pass #print('Problem with set_blocking() chunkyIO disabled')
                #self.chunkyIO=False
        if previousDirectory is not None:
            os.chdir(previousDirectory)
        # start reading the data
        def _readerThread(whichStream:int,ioObject:BytesIO):
            while self.running and not ioObject.closed:
                if not self.chunkyIO:
                    data=ioObject.read1(1)
                    if len(data)<1:
                        break
                    self.addBytes(whichStream,data)
                else:
                    data=ioObject.read(80)
                    if data:
                        self.addBytes(whichStream,data)
                    else:
                        if self._popen is None or self._popen.poll() is not None:
                            # We read nothing and the process has finished so there won't be more
                            break
                        time.sleep(0.005)
            ioObject.close()
            # last one out shuts down popen
            if self._popen is not None \
                and (self._popen.stdout is None or self._popen.stdout.closed)\
                and (self._popen.stderr is None or self._popen.stderr.closed):
                #
                self._running=False
                self.stop()
        self._outThread=Thread(target=_readerThread,
            args=(self.STDOUT,self._popen.stdout),
            daemon=useDaemonThreads)
        self._outThread.daemon=useDaemonThreads # thread shuts down when our thread does
        self._outThread.start()
        self._errThread=Thread(target=_readerThread,
            args=(self.STDERR,self._popen.stderr),
            daemon=useDaemonThreads)
        self._errThread.daemon=useDaemonThreads # thread shuts down when our thread does
        self._errThread.start()
        # returns immediately, leaving the program to run

    def stop(self):
        """
        stop the running program
        """
        RecieveDataManager.stop(self)
        if not self.running:
            return
        if self._popen is not None:
            print('TERMINATING "%s"'%self.osRun.cmd)
            self._popen.terminate()
            self._popen.kill()
            self._popen=None
        if self._outThread is not None:
            #self._outThread.stop()
            self._outThread=None
        if self._errThread is not None:
            #self._errThread.stop()
            self._errThread=None

    def __del__(self):
        """
        when we go out of scope, stop everything
        """
        self.stop()

    @property
    def result(self)->typing.Optional[OsRunResult]:
        """
        result of the program execution (can be None)
        """
        if self._result is None:
            stdout=self.getText(self.STDOUT)
            stderr=self.getText(self.STDERR)
            stdouterr=self.getText(self.STDOUTERR)
            result=OsRunResult(self._lastReturncode,stdout,stderr,stdouterr)
            if self.running:
                result.finished=False
                return result
            else:
                self._result=result
        return self._result

    def wait(self,timeout:typing.Optional[float]=None)->OsRunResult:
        """
        wait for the program to complete and return the result

        if maxWait=[seconds] expires, will stop the job and return as much
            data as it can get.  also result.finished will be False

        :throws TimeoutError: if maxWait is exceeded
        """
        remainingTime=timeout
        timeSleep=0.1
        while self.running:
            time.sleep(timeSleep)
            if remainingTime is not None:
                remainingTime-=timeSleep
                if remainingTime<=0:
                    raise TimeoutError()
        if self._popen is not None:
            if self._popen.returncode is None:
                self._lastReturncode=self._popen.wait() # sometimes there is a race cond where it has finished, but has not yet written the returncode # noqa: E501 # pylint: disable=line-too-long
            else:
                self._lastReturncode=self._popen.returncode
        result=self.result
        self.stop()
        if result is None:
            raise Exception("Never ran anything!")
        return result
