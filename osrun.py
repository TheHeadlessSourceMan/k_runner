"""
bit of an ease of use wrapper around subprocess.Popen()
"""
import typing
from collections.abc import Iterable
import os
import sys
from pathlib import Path
import subprocess
import time
from threading import Thread
import json
from stringTools import ansiColorToHtml, stripANSI

StringNotify=typing.Callable[[str],None]
StringNotifies=typing.Union[StringNotify,typing.Iterable[StringNotify]]
StringNotifyList=typing.List[StringNotify]

# my priority codes (0-100) low-high
LOWEST_PRIORITY=0
LOW_PRIORITY=0
LOWER_PRIORITY=25
BELOW_NORMAL_PRIORITY=25
NORMAL_PRIORITY=50
MEDIUM_PRIORITY=50
ABOVE_NORMAL_PRIORITY=75
HIGHER_PRIORITY=75
HIGH_PRIORITY=100
HIGHEST_PRIORITY=100
REALTIME_PRIORITY=101

def _getWindowsPriorityCode(pri:int)->int:
    """
    weirdly the values for windows priority
    codes don't follow any real pattern
    that I can see.
    """
    if pri<BELOW_NORMAL_PRIORITY:
        return 64
    if pri<NORMAL_PRIORITY:
        return 16384
    if pri<ABOVE_NORMAL_PRIORITY:
        return 32
    if pri<HIGH_PRIORITY:
        return 32768
    if pri<REALTIME_PRIORITY:
        return 128
    return 256

def _getWindowsWmicPriority(pri:int)->str:
    """
    for the wmic.exe command
    """
    if pri<BELOW_NORMAL_PRIORITY:
        return 'Low'
    if pri<NORMAL_PRIORITY:
        return 'Below normal'
    if pri<ABOVE_NORMAL_PRIORITY:
        return 'Normal'
    if pri<HIGH_PRIORITY:
        return 'Above normal'
    if pri<REALTIME_PRIORITY:
        return 'High'
    return 'Realtime'

def _getWindowsPriorityName(pri:int)->str:
    """
    For the start.exe command
    """
    if pri<BELOW_NORMAL_PRIORITY:
        return 'Low'
    if pri<NORMAL_PRIORITY:
        return 'BelowNormal'
    if pri<ABOVE_NORMAL_PRIORITY:
        return 'Normal'
    if pri<HIGH_PRIORITY:
        return 'AboveNormal'
    if pri<REALTIME_PRIORITY:
        return 'High'
    return 'Realtime'


def extendStringNotifies(
    extendThis:StringNotifyList,
    withThis:typing.Optional[StringNotifies]
    )->None:
    """
    Helper to add to a string notify list
    """
    if withThis is not None:
        if callable(withThis):
            extendThis.append(withThis)
        else:
            extendThis.extend(withThis)


def commandlineSplit(cmdline:typing.Union[str,typing.Iterable[str]]
    )->typing.Tuple[str,typing.List[str]]:
    """
    split a command line into a cmd,params[]
    (unquoting as necessary)
    """
    cmd=''
    params:typing.List[str]=[]
    if not isinstance(cmdline,str):
        first=True
        for c in params:
            if first:
                cmd=c
                first=False
            else:
                params.append(c) # pylint: disable=modified-iterating-list
        return (cmd,params)
    inQuot=''
    delimitNextQuote=False
    building=[]
    for c in cmdline:
        if inQuot:
            if c=='\\':
                if delimitNextQuote:
                    building.append('\\')
                else:
                    delimitNextQuote=True
            elif c==inQuot:
                if delimitNextQuote:
                    building.append(c)
                    delimitNextQuote=False
                else:
                    inQuot=''
            else:
                if delimitNextQuote:
                    building.append('\\')
                    delimitNextQuote=False
                building.append(c)
        else:
            if c in ('"',"'"):
                if delimitNextQuote:
                    building.append(c)
                    delimitNextQuote=False
                else:
                    inQuot=c
            elif c in (' ','\t','\r','\n'):
                if delimitNextQuote:
                    building.append('\\')
                    delimitNextQuote=False
                if building:
                    if not cmd:
                        cmd=''.join(building)
                    else:
                        params.append(''.join(building))
                    building=[]
            elif c=='\\':
                if delimitNextQuote:
                    building.append('\\')
                else:
                    delimitNextQuote=True
            else:
                if delimitNextQuote:
                    building.append('\\')
                    delimitNextQuote=False
                building.append(c)
    if building:
        if not cmd:
            cmd=''.join(building)
        else:
            params.append(''.join(building))
    return (cmd,params)


class OsRunResult:
    """
    result of an OsRun operation
    """

    def __init__(self,returncode:int,stdout:str,stderr:str,stdouterr:str):
        self.returncode:int=returncode
        self.stdout:str=stdout
        self.stderr:str=stderr
        self.stdouterr:str=stdouterr # stdout and stderr intermixed as you'd see it on the terminal # noqa: E501 # pylint: disable=line-too-long
        self.finished:bool=True

    def __eq__(self,v:typing.Any)->bool:
        if isinstance(v,(int,float)):
            return self.returncode==int(v)
        return False
    def __ne__(self,v:typing.Any)->bool:
        return not (self==v)

    @property
    def value(self)->int:
        """
        Get the return value (int) from the program
        """
        return self.returncode
    __int__=value
    __float__=value

    @property
    def json(self)->str:
        """
        Get these results as a json string
        """
        return json.dumps(self.jsonObj)
    @json.setter
    def json(self,jsonString:typing.Union[str,bytes]):
        if isinstance(jsonString,bytes):
            jsonString=jsonString.decode('utf-8','ignore')
        self.jsonObj=json.loads(jsonString)

    def __iter__(self):
        return iter(self.stdouterr.split('\n'))

    def __len__(self):
        return len(self.stdouterr)

    def __len_alt__(self):
        """
        overwriting this so that if statements work
        """
        if self.succeeded:
            return 1
        return 0

    @property
    def jsonObj(self)->typing.Dict[str,typing.Any]:
        """
        Return these results as a JSON-compatible object
        """
        ret:typing.Dict[str,typing.Any]={}
        ret['returncode']=self.returncode
        if not self.finished:
            ret['finished']=self.finished
        if self.stdout is not None and self.stdout:
            ret['stdout']=self.stdout
        if self.stderr is not None and self.stderr:
            ret['stderr']=self.stderr
        if self.stdouterr is not None and self.stdouterr:
            ret['stdouterr']=self.stdouterr
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.returncode=jsonObj.get('returncode','')
        self.finished=jsonObj.get('finished',True)
        self.stdout=jsonObj.get('stdout','')
        self.stderr=jsonObj.get('stderr','')
        self.stdouterr=jsonObj.get('stdouterr','')

    def load(self,filename:str)->None:
        """
        load these run results from a file
        """
        f=open(filename,'rb')
        self.json=f.read().decode('utf-8','ignore')
        f.close()

    def save(self,filename:str)->None:
        """
        save these run results to a file
        """
        f=open(filename,'wb')
        f.write(self.json.encode('utf-8'))
        f.close()

    def __cmp__(self,other):
        """
        can do
            ==bool # for whether or not the result was successful
            ==int # to compare against returncode
            ==str # to compare a string against the combined string buffer
            ==OsRunResult # to see if this matches exactly another result
        """
        if isinstance(other,bool):
            return self.succeeded==other
        if isinstance(other,int):
            return self.returncode==other
        if isinstance(other,str):
            return self.stdouterr==other
        if isinstance(other,OsRunResult):
            return (self.returncode==other.returncode and
                self.finished==other.finished and
                self.stdouterr==other.stdouterr and
                self.stdout==other.stdout and
                self.stderr==other.stderr)
        raise TypeError()

    @property
    def out(self):
        """
        same as stdout
        """
        return self.stdout
    stdOut=out
    stdOutLines=out
    stdoutlines=out
    stdoutLines=out

    @property
    def err(self):
        """
        same as stderr
        """
        return self.stderr
    stdErr=err
    stdErrLines=err
    stderrlines=err

    @property
    def stdOutErr(self):
        """
        Combined stdout and stderr
        """
        return self.stdouterr
    stdOuterr=stdOutErr
    stdOutErrLines=stdOutErr
    stdOuterrlines=stdOutErr
    outErr=stdOutErr
    outerr=stdOutErr
    outerrLines=stdOutErr
    outErrLines=stdOutErr

    @property
    def succeeded(self):
        """
        judging by the returncode and stderr,
        determine if the command succeeded

        NOTE: assumption not always the case.
        be sure to check your command's documentation before using.
        """
        return self.returncode==0 and not self.stderr

    @property
    def failed(self):
        """
        judging by the returncode and stderr,
        determine if the command succeeded

        NOTE: assumption not always the case.
        Be sure to check your command's documentation before using.
        """
        return not self.succeeded

    def __repr__(self):
        return self.stdouterr
OsRunResults=OsRunResult


class OsRunBuf:
    """
    A buffer used to gather up bytes from a process

    (typically, a process would have stdout,stderr, and combined buffers)
    """

    def __init__(self,
        callOnChar:typing.Optional[StringNotifies]=None,
        callOnLine:typing.Optional[StringNotifies]=None,
        ansiHandling:str="strip"
        ):
        """
        :param ansiHandling: how to handle ansi escape codes
            "strip"(default), "preserve", or "html"
        """
        self.ansiHandling=ansiHandling
        self.done:bool=False
        self._ansiStateMachine:int=0
        self._line:bytearray=bytearray()
        self._lines:typing.List[bytes]=[] # that's a list of groups of bytes
        self.callOnChar:StringNotifyList=[]
        self.callOnLine:StringNotifyList=[]
        self.addCallOnLine(callOnLine)
        self.addCallOnChar(callOnChar)
        self.encoding='utf-8' # one of the standard encodings https://docs.python.org/3/library/codecs.html#standard-encodings # noqa: E501 # pylint: disable=line-too-long

    def addCallOnLine(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        extendStringNotifies(self.callOnLine,addThis)

    def addCallOnChar(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        extendStringNotifies(self.callOnChar,addThis)

    def clear(self)->None:
        """
        Clear this buffer
        """
        self._line=bytearray()
        self._lines=[]

    def append(self,data:bytes)->None:
        """
        add bytes to the buffer
        """
        if data is None or not data:
            return
        for b in data:
            if b==13: # aka '\r' to mitigate CRLF nonsense
                continue
            if self.callOnChar is not None:
                q=bytes(b).decode(self.encoding,'ignore')
                for c in self.callOnChar:
                    c(q)
            if self._ansiStateMachine==27:
                self._line.append(b)
                if b==b'[':
                    self._ansiStateMachine=b
                else:
                    self._ansiStateMachine=0
            elif self._ansiStateMachine==b'[':
                self._line.append(b)
                if b==b'm':
                    self._ansiStateMachine=0
            else:
                if b==27: # escape starts ansi sequence
                    self._line.append(b) # we keep the escape codes!
                    self._ansiStateMachine=27
                elif b==10: # aka '\n'
                    self._lines.append(self._line)
                    if self.callOnLine:
                        line=self._interpret(self._line)
                        for c in self.callOnLine:
                            c(line)
                    self._line.clear()
                else:
                    self._line.append(b)

    def _interpret(self,data:bytes)->str:
        """
        Interpret a sequence of bytes as a string,
        according to how we want to handle ansi escape codes
        """
        if self.ansiHandling=='strip':
            return stripANSI(data)
        if self.ansiHandling=='html':
            return ansiColorToHtml(data)
        return data.decode('utf-8',errors='ignore')

    def lineIter(self)->typing.Generator[str,None,None]:
        """
        iterate over the result lines as they come in
        until the done flag is set
        """
        from queue import Queue,Empty
        q:Queue=Queue()
        def cb(line):
            q.put(line)
        self.callOnLine.append(cb)
        while True:
            try:
                data=q.get(timeout=0.1)
                if data is None:
                    raise Exception()
                yield data
            except Empty:
                if self.done:
                    break
    __iter__=lineIter

    def toString(self)->str:
        """
        Convert this buffer to a string
        """
        if self._line:
            self._lines.append(self._line)
            self._line.clear()
        return self._interpret(
            b'\n'.join([line for line in self._lines]).strip())
    def __repr__(self)->str:
        return self.toString()

    def __cmp__(self,other:typing.Any)->bool:
        """
        other will be converted to string
        """
        if not isinstance(other,str):
            other=str(other)
        return other==str(self)


class OsRunException(Exception):
    """
    Thrown when there is a problem running a given command
    """
    def __init__(self,
        cmd:typing.List[str],
        cause:typing.Optional[Exception]=None):
        """ """
        self.cmd=cmd
        self.cause=cause
        msg=f'Trouble running:\n\t{cmd}'
        if cause is not None:
            aMsg=[f'{msg}\nCaused by:']
            aMsg.extend(str(cause).split('\n'))
            msg='\n\t'.join(aMsg)
        Exception.__init__(self,msg)


class OsRunJob:
    """
    Starts a new job running and collects the results.
    """
    def __init__(self,
        osRun:"OsRun",
        callOnStdoutLine:typing.Optional[StringNotifies]=None,
        callOnStderrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutErrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutChar:typing.Optional[StringNotifies]=None,
        callOnStderrChar:typing.Optional[StringNotifies]=None,
        callOnStdoutErrChar:typing.Optional[StringNotifies]=None):
        """ """
        self._result:typing.Optional[OsRunResult]=None
        self.running:bool=False
        self.outBuf:OsRunBuf=OsRunBuf(
            callOnLine=callOnStdoutLine,callOnChar=callOnStdoutChar)
        self.errBuf:OsRunBuf=OsRunBuf(
            callOnLine=callOnStderrLine,callOnChar=callOnStderrChar)
        self.outerrBuf:OsRunBuf=OsRunBuf(
            callOnLine=callOnStdoutErrLine,callOnChar=callOnStdoutErrChar)
        self._outThread:typing.Optional[Thread]=None
        self._errThread:typing.Optional[Thread]=None
        self._popen:typing.Optional[subprocess.Popen]=None
        self._lastReturncode:int=-9999
        self.workingDirectory:typing.Optional[Path]=None
        if osRun.workingDirectory is not None:
            # keep a copy in case they change it
            self.workingDirectory=Path(osRun.workingDirectory)
        self.osRun=osRun

    def addCallOnStdoutLine(self,
        addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        self.outBuf.addCallOnLine(addThis)

    def addCallOnStdoutChar(self,
        addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        self.outBuf.addCallOnChar(addThis)

    def addCallOnStderrLine(self,
        addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        self.errBuf.addCallOnLine(addThis)

    def addCallOnStderrChar(self,
        addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        self.errBuf.addCallOnChar(addThis)

    def addCallOnStdoutErrLine(self,
        addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        self.outerrBuf.addCallOnLine(addThis)

    def addCallOnStdoutErrChar(self,
        addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        self.outerrBuf.addCallOnChar(addThis)

    @property
    def pid(self)->typing.Optional[int]:
        """
        returns the process id
        if not running, returns None
        """
        if self._popen is None:
            return None
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
        workingDirectory:typing.Union[None,str,Path]=None)->None:
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
        self.running=True
        self._result=None
        self.outBuf.clear()
        self.errBuf.clear()
        self.outerrBuf.clear()
        # set up debugging
        if self.debugLog in self.outerrBuf.callOnLine: # print is registered
            if not self.osRun.debug: # we don't want do debug
                self.outerrBuf.callOnLine.remove(self.debugLog) # remove it
        else: # print is not registered
            if self.osRun.debug: # we do want to debug
                self.outerrBuf.callOnLine.append(self.debugLog) #register it
        # build up the command to be run
        if workingDirectory is None:
            if self.workingDirectory is None:
                workingDirectory=Path(os.getcwd()).absolute()
            else:
                workingDirectory=self.workingDirectory
        else:
            workingDirectory=Path(workingDirectory).absolute()
        cmd:typing.List[str]=[self.osRun.cmd]
        cmd.extend(self.osRun.params)
        if moreParams is not None:
            cmd.extend(moreParams)
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
                msg=f'Unable to access "{workingDirectory}"'
                raise FileNotFoundError(msg) from e
        if self.osRun.priority!=MEDIUM_PRIORITY:
            if os.name=='nt':
                # of the form:
                #     start "" /AboveNormal "C:\Windows\System32\mspaint.exe"
                # see also:
                # https://www.tenforums.com/tutorials/89548-set-cpu-process-priority-applications-windows-10-a.html
                if workingDirectory is None:
                    cmdPath=Path(cmd[0]).absolute()
                else:
                    cmdPath=workingDirectory/cmd[0]
                if not cmdPath.is_file():
                    cmdPath=Path(cmd[0])
                winPri=_getWindowsPriorityName(self.osRun.priority)
                newCmd=['start','',f'/{winPri}',str(cmdPath)]
                if len(cmd)>1:
                    newCmd.extend(cmd[1:])
                cmd=newCmd
                self.osRun.shell=True
                self.osRun.debug=True # TODO: temporary
            else:
                # TODO: not sure how to do this.
                # Maybe the "nice" command or something??
                raise NotImplementedError()
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
            print('$> ',' '.join(cmd))
        try:
            # NOTE: the following throws a warning message,
            # thus the workaround below.
            # see:
            #    https://bugs.python.org/issue32236
            #self._popen=subprocess.Popen(cmd,
            #    shell=self.osRun.shell,
            #    stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            #    bufsize=1,creationflags=creationflags,cwd=workingDirectory)
            self._popen=subprocess.Popen(cmd,
                shell=self.osRun.shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                creationflags=creationflags,
                cwd=str(workingDirectory),
                env=self.osRun.env,
                startupinfo=startupinfo
                )
        except Exception as e:
            raise OsRunException(cmd,e) from e
        if previousDirectory is not None:
            os.chdir(previousDirectory)
        # start reading the data
        def _readerThread(stream,bufA,bufB):
            while self.running:
                data=stream.read1(1)
                if len(data)<1:
                    break
                bufA.append(data)
                bufB.append(data)
            stream.close()
            bufB.done=True
            # last one out shuts down popen
            if self._popen is not None \
                and (self._popen.stdout is None or self._popen.stdout.closed)\
                and (self._popen.stderr is None or self._popen.stderr.closed):
                #
                self.running=False
                bufA.done=True
        self._outThread=Thread(target=_readerThread,
            args=(self._popen.stdout,self.outerrBuf,self.outBuf))
        self._outThread.daemon=True # thread shuts down when our thread does
        self._outThread.start()
        self._errThread=Thread(target=_readerThread,
            args=(self._popen.stderr,self.outerrBuf,self.errBuf))
        self._errThread.daemon=True # thread shuts down when our thread does
        self._errThread.start()
        # returns immediately, leaving the program to run

    def stop(self):
        """
        stop the running program
        """
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
            stdout=str(self.outBuf)
            stderr=str(self.errBuf)
            stdouterr=str(self.outerrBuf)
            result=OsRunResult(self._lastReturncode,stdout,stderr,stdouterr)
            if self.running:
                result.finished=False
                return result
            else:
                self._result=result
        return self._result

    def wait(self,maxWait:typing.Optional[float]=None)->OsRunResult:
        """
        wait for the program to complete and return the result

        if maxWait=[seconds] expires, will stop the job and return as much
            data as it can get.  also result.finished will be False

        :throws TimeoutError: if maxWait is exceeded
        """
        remainingTime=maxWait
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


class OsRun:
    """
    Run a system application.

    Handy shortcuts:

        # simplest way to run a command and get the results
        results=OsRun(cmdline).run()

        results=OsRun(cmdline)() # even shorter way of doing the same thing
        results=OsRun(cmdline,shell=True)() # run with a shell environment
        results=OsRun(cmdline,args[]).run() # run with arguments
        results=OsRun(cmdline).run(args[]) # run with arguments after the fact

        # print any errors and do the code if there are none
        if OsRun(cmdline).poe(args[]):
            ...

        # if you want to run and catch each line as it comes out
        for line in OsRun(cmdline):
            ... # do something

        # start up multiple instances from one OsRun specification.
        imageFilenames=[]
        # if you don't want them to shut down when jobs[]
        # goes out of scope you could add detach=True
        gimp=OsRun("gimp")
        jobs=[gimp.runAsync(filename) for filename in imageFilenames]
        for job in jobs:
            job.wait()

        try:
            # time out if the program takes too long
            results=OsRun(cmdline).run(maxWait=60)
        except TimeoutError:
            pass

    Shortcuts for dealing with results:
        if results.success:
            print(results.stdout) # print just the stdout
        else:
            print(results.stderr) # print just the stderr

        if results: # same as results.success

            ...

        print(results.stdouterr) # print both in their correct order
        print(results) # same, but simpler to read

    Run modes:
        run()->OsRunResult
            start and block until completion, terminate program
            if object is deleted (which is unlikely)
            use if you need the program to complete
            or its output before proceeding
        runAsync()->OsRunJob
            start in bg and move on with this thread, terminate program
            if object is deleted
            use if you need to do something else while the program is running
        detach runAsync()->None
            run even if the object (or even the creator app) goes out of scope
            use for starting other applications that will out-live your own
        detach run()
            Not allowed (doesn't make sense)
    """

    def __init__(self,
        cmd:typing.Union[str,typing.Iterable[str]],
        params:typing.Optional[typing.Iterable[str]]=None,
        shell:bool=False,
        detach:bool=False,
        debug:bool=False,
        cmdLineSplit:typing.Optional[bool]=None,
        workingDirectory:typing.Union[None,str,Path]=None,
        env:typing.Optional[typing.Dict[str,typing.Any]]=None,
        callOnStdoutLine:typing.Optional[StringNotifies]=None,
        callOnStderrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutErrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutChar:typing.Optional[StringNotifies]=None,
        callOnStderrChar:typing.Optional[StringNotifies]=None,
        callOnStdoutErrChar:typing.Optional[StringNotifies]=None,
        priority:int=MEDIUM_PRIORITY,
        ansiHandling:str="strip",
        showHidden:bool=False,
        showMinimized:bool=False,
        showMaximized:bool=False
        ):
        """
        :param workingDirectory: perform the operation in a specific directory
            * NOTE: there may be issues with multiple simultaneous programs
        :param cmdLineSplit: how and when to split cmd parameter
            if True will always attempt to split cmd into params
            if False will not
            if None (default) will only attempt if params[] is None
        :param ansiHandling: how to handle ansi escape codes
            "strip"(default), "preserve", or "html"
        """
        self.ansiHandling=ansiHandling
        useParams:typing.List[str]=[]
        if cmd is not None \
            and isinstance(cmd,Iterable) \
            and not isinstance(cmd,str):
            #
            cmd=list(cmd)
            # they mistakenly sent in all args in the cmd
            if len(cmd)>1:
                params=cmd[1:]
            cmd=cmd[0]
        if cmdLineSplit is None:
            if params is None:
                cmd,useParams=commandlineSplit(cmd)
        elif cmdLineSplit:
            cmd,useParams=commandlineSplit(cmd)
        if not isinstance(cmd,str):
            cmd,useParams=commandlineSplit(cmd)
        if params is not None:
            useParams.extend(params)
        self.priority=priority
        self.params:typing.List[str]=useParams # params to pass to the command
        self.cmd:str=cmd # command to run
        self.shell:bool=shell # run in the system shell environment (slower and usually unnecessary) # noqa: E501 # pylint: disable=line-too-long
        self.detach:bool=detach # detach from this process/run in background
        self.debug:bool=debug # print the command input and output for debugging # noqa: E501 # pylint: disable=line-too-long
        self.workingDirectory:typing.Optional[Path]=None
        if workingDirectory is not None:
            self.workingDirectory=Path(workingDirectory).absolute()
        if env is None:
            env=dict(os.environ)
        self.env:typing.Dict[str,typing.Any]=env
        self.callOnStdoutLine:StringNotifyList=[]
        self.callOnStderrLine:StringNotifyList=[]
        self.callOnStdoutErrLine:StringNotifyList=[]
        self.callOnStdoutChar:StringNotifyList=[]
        self.callOnStderrChar:StringNotifyList=[]
        self.callOnStdoutErrChar:StringNotifyList=[]
        self.addCallOnStdoutLine(callOnStdoutLine)
        self.addCallOnStderrLine(callOnStderrLine)
        self.addCallOnStdoutErrLine(callOnStdoutErrLine)
        self.addCallOnStdoutChar(callOnStdoutChar)
        self.addCallOnStderrChar(callOnStderrChar)
        self.addCallOnStdoutErrChar(callOnStdoutErrChar)
        self.showHidden=showHidden
        self.showMinimized=showMinimized
        self.showMaximized=showMaximized

    def addCallOnStdoutLine(self,
        addThis:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new line of data
        """
        extendStringNotifies(self.callOnStdoutLine,addThis)

    def addCallOnStdoutChar(self,
        addThis:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new char of data
        """
        extendStringNotifies(self.callOnStdoutChar,addThis)

    def addCallOnStderrLine(self,
        addThis:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new line of data
        """
        extendStringNotifies(self.callOnStderrLine,addThis)

    def addCallOnStderrChar(self,
        addThis:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new char of data
        """
        extendStringNotifies(self.callOnStderrChar,addThis)

    def addCallOnStdoutErrLine(self,
        addThis:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new line of data
        """
        extendStringNotifies(self.callOnStdoutErrLine,addThis)

    def addCallOnStdoutErrChar(self,
        addThis:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new char of data
        """
        extendStringNotifies(self.callOnStdoutErrChar,addThis)

    @property
    def json(self)->str:
        """
        This run as a json string
        """
        return json.dumps(self.jsonObj)
    @json.setter
    def json(self,jsonString:typing.Union[str,bytes]):
        if isinstance(jsonString,bytes):
            jsonString=jsonString.decode('utf-8','ignore')
        self.jsonObj=json.loads(jsonString)

    @property
    def jsonObj(self)->typing.Dict[str,typing.Any]:
        """
        This run as a json-compatible object
        """
        ret:typing.Dict[str,typing.Any]={'cmd':self.cmd}
        if self.params:
            ret['params']=self.params
        if self.shell:
            ret['shell']=self.shell
        if self.detach:
            ret['detach']=self.detach
        if self.debug:
            ret['debug']=self.debug
        if self.workingDirectory is not None and self.workingDirectory:
            ret['workingDirectory']=str(self.workingDirectory)
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.cmd=jsonObj.get('cmd','')
        self.params=jsonObj.get('params',[])
        self.shell=jsonObj.get('shell',False)
        self.detach=jsonObj.get('detach',False)
        self.debug=jsonObj.get('debug',False)
        wd=jsonObj.get('workingDirectory',None)
        if wd is not None:
            wd=Path(wd)
        self.workingDirectory=wd

    def load(self,filename:str)->None:
        """
        load this run configuration from a file

        NOTE: to load the results from a file see OsRunResult.load()
        """
        f=open(filename,'rb')
        self.json=f.read().decode('utf-8','ignore')
        f.close()

    def save(self,filename:str)->None:
        """
        save this run configuration to a file

        NOTE: to save the results to a file see OsRunResult.save()
        """
        f=open(filename,'wb')
        f.write(self.json.encode('utf-8'))
        f.close()

    def __call__(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None,
        maxWait:typing.Optional[float]=None
        )->OsRunResult:
        """
        shortcut for run()

        returns (returncode,stdout,stderr,stdouterr)
        """
        return self.run(moreParams,workingDirectory,maxWait)

    def run(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None,
        maxWait:typing.Optional[float]=None,
        callOnStdoutLine:typing.Optional[StringNotifies]=None,
        callOnStderrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutErrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutChar:typing.Optional[StringNotifies]=None,
        callOnStderrChar:typing.Optional[StringNotifies]=None,
        callOnStdoutErrChar:typing.Optional[StringNotifies]=None
        )->OsRunResult:
        """
        run the command and return the results

        returns OsRunResult

        :throws TimeoutError: if maxWait is exceeded

        NOTE: this is literally the same thing as runAsync().wait()
        """
        if self.detach:
            raise Exception(
                'For detached process, only runAsync() is supported!')
        job=self.runAsync(
            moreParams,
            workingDirectory,
            callOnStdoutLine,
            callOnStderrLine,
            callOnStdoutErrLine,
            callOnStdoutChar,
            callOnStderrChar,
            callOnStdoutErrChar)
        ret=job.wait(maxWait)
        return ret

    def poe(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None,
        maxWait:typing.Optional[float]=None
        )->OsRunResult:
        """
        stands for "print only errors"

        returns OsRunResult

        NOTE: any TimeoutError generated will be converted to an OsResult

        """
        try:
            ret=self.run(moreParams,workingDirectory,maxWait)
        except TimeoutError:
            errStr="ERR: job took longer than %s sec and was killed."%str(maxWait) # noqa: E501 # pylint: disable=line-too-long
            ret=OsRunResult(-2400,'',errStr,errStr)
        if ret.failed:
            print(ret,file=sys.stderr)
        return ret

    def runAsync(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None,
        callOnStdoutLine:typing.Optional[StringNotifies]=None,
        callOnStderrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutErrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutChar:typing.Optional[StringNotifies]=None,
        callOnStderrChar:typing.Optional[StringNotifies]=None,
        callOnStdoutErrChar:typing.Optional[StringNotifies]=None
        )->OsRunJob:
        """
        run the command asynchronously

        returns RunJob object representing the current job

        NOTE: if RunJob is garbage collected, the job itself will terminate
        """
        job=OsRunJob(self,
            callOnStdoutLine=self.callOnStdoutLine,
            callOnStderrLine=self.callOnStderrLine,
            callOnStdoutErrLine=self.callOnStdoutErrLine,
            callOnStdoutChar=self.callOnStdoutChar,
            callOnStderrChar=self.callOnStderrChar,
            callOnStdoutErrChar=self.callOnStdoutErrChar)
        job.addCallOnStdoutLine(callOnStdoutLine)
        job.addCallOnStderrLine(callOnStderrLine)
        job.addCallOnStdoutErrLine(callOnStdoutErrLine)
        job.addCallOnStdoutChar(callOnStdoutChar)
        job.addCallOnStderrChar(callOnStderrChar)
        job.addCallOnStdoutErrChar(callOnStdoutErrChar)
        job.start(moreParams,workingDirectory)
        return job

    def runIterAllOutput(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None
        )->typing.Generator[str,None,None]:
        """
        The idea is you run the command and get the lines back
        one at a time as an iterator

        for line in OsRun("ps -A").runIterAllOutput():
            ...

        NOTE: if you don't care about moreParams or maxWait,
            you can get even simpler, eg:
            for line in OsRun("ps -A"):
                ...
        """
        job=OsRunJob(self)
        it=job.outerrBuf.lineIter()
        job.start(moreParams,workingDirectory)
        yield from it

    def runIterStdout(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None
        )->typing.Generator[str,None,None]:
        """
        The idea is you run the command and get the stdout lines
        back one at a time as an iterator

        for line in OsRun("ps -A").runIterStdout():
            ...

        NOTE: runIterAllOutput() gets both stdout and stderr mixed
        """
        job=OsRunJob(self)
        it=job.outBuf.lineIter()
        job.start(moreParams,workingDirectory)
        yield from it

    def runIterStderr(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Union[None,str,Path]=None
        )->typing.Generator[str,None,None]:
        """
        The idea is you run the command and get the stderr
        lines back one at a time as an iterator

        for line in OsRun("ps -A").runIterStderr():
            ...

        NOTE: runIterAllOutput() gets both stdout and stderr mixed
        """
        job=OsRunJob(self)
        it=job.errBuf.lineIter()
        job.start(moreParams,workingDirectory)
        yield from it

    def __iter__(self)->typing.Iterator[str]:
        """
        shortcut for runIterAllOutput()
        """
        return self.runIterAllOutput()


def osrun(
    cmd:typing.Union[str,typing.Iterable[str]],
    params:typing.Optional[typing.Iterable[str]]=None,
    shell:bool=False,
    detach:bool=False,
    debug:bool=False,
    cmdLineSplit:typing.Optional[bool]=None,
    workingDirectory:typing.Union[None,str,Path]=None,
    env:typing.Optional[typing.Dict[str,typing.Any]]=None,
    callOnStdoutLine:typing.Optional[StringNotifies]=None,
    callOnStderrLine:typing.Optional[StringNotifies]=None,
    callOnStdoutErrLine:typing.Optional[StringNotifies]=None,
    callOnStdoutChar:typing.Optional[StringNotifies]=None,
    callOnStderrChar:typing.Optional[StringNotifies]=None,
    callOnStdoutErrChar:typing.Optional[StringNotifies]=None
    )->OsRunResult:
    """ shortcut for OsRun().run(...) """
    return OsRun(cmd,
        params,shell,
        detach,debug,
        cmdLineSplit,
        workingDirectory,
        env,
        callOnStdoutLine,
        callOnStderrLine,
        callOnStdoutErrLine,
        callOnStdoutChar,
        callOnStderrChar,
        callOnStdoutErrChar).run()
run=osrun

def cmdline(args:typing.Iterable[str])->int:
    """
    Run this like from the command line
    """
    printHelp=False
    shell=False
    detach=False
    maxWait=None
    useIter=True # whether to iterate on each line or dump them all at the end
    dashMode=False
    dashModeCmd=''
    dashModeArgs=[]
    for arg in args:
        if dashMode:
            if arg:
                if not dashModeCmd:
                    dashModeCmd=arg
                else:
                    dashModeArgs.append(arg)
        elif arg.startswith('-'):
            av=arg.split('=',1)
            if av[0]=='-':
                dashMode=True
            elif av[0]=='--help':
                printHelp=True
            elif av[0]=='--shell':
                if len(av)<2:
                    shell=True
                else:
                    shell=av[1][0].lower() in ('1','t','y')
            elif av[0]=='--detach':
                if len(av)<2:
                    detach=True
                else:
                    detach=av[1][0].lower() in ('1','t','y')
            elif av[0]=='--maxWait':
                if len(av)<2:
                    maxWait=None
                else:
                    maxWait=float(av[1])
            else:
                print('ERR: Unknown Argument "%s"'%arg)
                printHelp=True
        else:
            osr=OsRun(arg,shell=shell,detach=detach,debug=False)
            if useIter:
                for line in osr:
                    print(line)
            else:
                results=osr(maxWait=maxWait)
                print(results)
    if dashMode:
        osr=OsRun(
            dashModeCmd,
            dashModeArgs,
            shell=shell,
            detach=detach,
            debug=False)
        if useIter:
            for line in osr:
                print(line)
        else:
            results=osr(maxWait=maxWait)
            print(results)
    if printHelp:
        print('Usage:')
        print('   osrun.py [options] "[cmd params]" ...')
        print('Options:')
        print('   --help .............. show this help')
        print('   --shell ............. run with a shell environment')
        print('   --maxWait=sec ...... how long to wait for the program')
        print('   --detach ........... run detached from this console (closing console will not close program)') # noqa: E501 # pylint: disable=line-too-long
        print('   - ................... everything after this point is cmd+params (convenience to not have to quote everything)') # noqa: E501 # pylint: disable=line-too-long
        print('NOTE:')
        print('   files and options are evaluated IN ORDER')
        return -1
    return 0


if __name__=='__main__':
    sys.exit(cmdline(sys.argv[1:]))
