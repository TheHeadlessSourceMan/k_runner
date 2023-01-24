"""
bit of an ease of use wrapper around subprocess.Popen()
"""
import typing
import os
import sys
import subprocess
import time
from threading import Thread
import json

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


def _getWinowsPriorityCode(pri:int)->int:
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

def _getWinowsWmicPriority(pri:int)->str:
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

def _getWinowsPriorityName(pri:int)->str:
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


def extendStringNotifies(extendThis:StringNotifyList,withThis:typing.Optional[StringNotifies])->None:
    if withThis is not None:
        if callable(withThis):
            extendThis.append(withThis)
        else:
            extendThis.extend(withThis)
            

def commandlineSplit(cmdline:str)->typing.Tuple[str,typing.List[str]]:
    """
    split a command line into a cmd,params[]
    (unquoting as necessary)
    """
    inQuot=''
    delimitNextQuote=False
    cmd=''
    params:typing.List[str]=[]
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
        self.stdouterr:str=stdouterr # stdout and stderr intermixed as you'd see it on the terminal
        self.finished:bool=True
        
    def __eq__(self,v:typing.Any)->bool:
        return self.returncode==int(v)
    def __ne__(self,v:int)->bool:
        return self.returncode!=v
    
    @property
    def value(self)->int:
        return self.returncode
    __int__=value
    __float__=value
    
    @property
    def json(self)->str:
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
        ret:typing.Dict[str,typing.Any]={}
        ret['returncode']=self.returncode
        if not self.finished:
            ret['finished']=self.finished
        if self.stdout is not None:
            ret['stdout']=self.stdout
        if self.stdout is not None:
            ret['stderr']=self.stdout
        if self.stdout is not None:
            ret['stdouterr']=self.stdout
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.returncode=jsonObj.get('returncode','')
        self.finished=jsonObj.get('finished',True)
        self.stdout=jsonObj.get('stdout',None)
        self.stderr=jsonObj.get('stderr',None)
        self.stdouterr=jsonObj.get('stdouterr',None)

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
        
        NOTE: assumption not always the case.  be sure to check your command's documentation before using.
        """
        return self.returncode==0 and not self.stderr
        
    @property
    def failed(self):
        """
        judging by the returncode and stderr,
        determine if the command succeeded
        
        NOTE: assumption not always the case.  be sure to check your command's documentation before using.
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
        callOnLine:typing.Optional[StringNotifies]=None):
        """ """
        self.done:bool=False
        self._line:typing.List[bytes]=[]
        self._lines:typing.List[bytes]=[]
        self.callOnChar:StringNotifyList=[]
        self.callOnLine:StringNotifyList=[]
        self.addCallOnLine(callOnLine)
        self.addCallOnChar(callOnChar)
        self.encoding='utf-8' # one of the standard encodings https://docs.python.org/3/library/codecs.html#standard-encodings
        
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
        self._line=[]
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
            if b==10: # aka '\n'
                line=b''.join(self._line)
                self._lines.append(line)
                self._line.clear()
                if self.callOnLine:
                    q=line.decode(self.encoding,'ignore')
                    for c in self.callOnLine:
                        c(q)
            else:
                self._line.append(data)
    
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
        if self._line:
            self._lines.append(b''.join(self._line))
            self._line.clear()
        return b'\n'.join(self._lines).strip().decode(self.encoding,'ignore')
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
    def __init__(self,cmd:typing.List[str],cause:typing.Optional[Exception]=None):
        self.cmd=cmd
        self.cause=cause
        msg=f'Trouble running:\n\t{cmd}'
        if cause is not None:
            amsg=[f'{msg}\nCaused by:']
            amsg.extend(str(cause).split('\n'))
            msg='\n\t'.join(amsg)
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
        self.outBuf:OsRunBuf=OsRunBuf(callOnLine=callOnStdoutLine,callOnChar=callOnStdoutChar)
        self.errBuf:OsRunBuf=OsRunBuf(callOnLine=callOnStderrLine,callOnChar=callOnStderrChar)
        self.outerrBuf:OsRunBuf=OsRunBuf(callOnLine=callOnStdoutErrLine,callOnChar=callOnStdoutErrChar)
        self._outThread:typing.Optional[Thread]=None
        self._errThread:typing.Optional[Thread]=None
        self._popen:typing.Optional[subprocess.Popen]=None
        self._lastReturncode:int=-9999
        self.workingDirectory:typing.Optional[str]=osRun.workingDirectory # keep a copy in case they change it
        self.osRun=osRun
    
    def addCallOnStdoutLine(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        self.outBuf.addCallOnLine(addThis)
        
    def addCallOnStdoutChar(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        self.outBuf.addCallOnChar(addThis)
    
    def addCallOnStderrLine(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        self.errBuf.addCallOnLine(addThis)
        
    def addCallOnStderrChar(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        self.errBuf.addCallOnChar(addThis)
    
    def addCallOnStdoutErrLine(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        self.outerrBuf.addCallOnLine(addThis)
        
    def addCallOnStdoutErrChar(self,addThis:typing.Optional[StringNotifies]=None)->None:
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
        if self._popen is not None:
            v=' '.join([str(v) for v in vals])
            self._popen.stdin.write(v)
            self._popen.stdin.flush()
    def writeln(self,*vals):
        if self._popen is not None:
            v=' '.join([str(v) for v in vals])
            self._popen.stdin.write(v)
            self._popen.stdin.write('\n')
            self._popen.stdin.flush()
    print=writeln

    def start(self,moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None)->None:
        """
        start the thing running

        :moreParams: add more parameters in addition to the ones specified in the constructor
            the idea is you could set up the command the way you want it, then run on multiple files
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
            workingDirectory=self.workingDirectory
        cmd:typing.List[str]=[self.osRun.cmd]
        cmd.extend(self.osRun.params)
        if moreParams is not None:
            cmd.extend(moreParams)
        # launch the program
        creationflags=0
        if self.osRun.detatch:
            DETACHED_PROCESS=0x00000008
            creationflags=DETACHED_PROCESS
        previousDirectory=None
        if workingDirectory:
            previousDirectory=os.getcwd()
            os.chdir(workingDirectory)
        if self.osRun.priority!=MEDIUM_PRIORITY:
            if os.name=='nt':
                # of the form:
                #     start "" /AboveNormal "C:\Windows\System32\mspaint.exe"
                # see also: https://www.tenforums.com/tutorials/89548-set-cpu-process-priority-applications-windows-10-a.html
                if workingDirectory is None:
                    cmdpath=os.path.abspath(cmd[0])
                else:
                    cmdpath=os.path.abspath(os.sep.join((workingDirectory,cmd[0])))
                if not os.path.isfile(cmdpath):
                    cmdpath=cmd[0]
                winPri=_getWinowsPriorityName(self.osRun.priority)
                newCmd=['start','',f'/{winPri}',cmdpath]
                if len(cmd)>1:
                    newCmd.extend(cmd[1:])
                cmd=newCmd
                self.osRun.shell=True
                self.osRun.debug=True # TODO: temporary
            else:
                # not sure how to do this.  Maybe the "nice" command or something??
                raise NotImplementedError()
        if self.osRun.debug:
            print('$> ',' '.join(cmd))
        try:
            # NOTE: the following throws a warning message, thus the workaround.
            # see:
            #    https://bugs.python.org/issue32236
            #self._popen=subprocess.Popen(cmd,shell=self.osRun.shell,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
            #    bufsize=1,creationflags=creationflags,cwd=workingDirectory)
            self._popen=subprocess.Popen(cmd,shell=self.osRun.shell,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,creationflags=creationflags,cwd=workingDirectory,env=self.osRun.env)
        except Exception as e:
            raise OsRunException(cmd,e)
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
            if self._popen is not None and self._popen.stdout.closed and self._popen.stderr.closed:
                self.running=False
                bufA.done=True
        self._outThread=Thread(target=_readerThread,args=(self._popen.stdout,self.outerrBuf,self.outBuf))
        self._outThread.daemon=True # thread should shutdown when our thread does
        self._outThread.start()
        self._errThread=Thread(target=_readerThread,args=(self._popen.stderr,self.outerrBuf,self.errBuf))
        self._errThread.daemon=True # thread should shutdown when our thread does
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
                self._lastReturncode=self._popen.wait() # sometimes there is a race cond where it has finished, but has not yet written the returncode
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
        results=OsRun(cmdline).run() # simplest way to run a command and get the results
        results=OsRun(cmdline)() # even shorter way of doing the same thing
        results=OsRun(cmdline,shell=True)() # run with a shell environment
        results=OsRun(cmdline,args[]).run() # run with arguments
        results=OsRun(cmdline).run(args[]) # run with arguments after the fact

        if OsRun(cmdline).poe(args[]): # print any errors and do the code if there are none
            ...

        for line in OsRun(cmdline): # if you want to run and catch each line as it comes out
            ... # do something
        
        # start up multiple instances from one OsRun specification.
        imageFilenames=[]
        gimp=OsRun("gimp") # if you don't want them to shut down when jobs[] goes out of scope you could add detatch=True
        jobs=[gimp.runAsync(filename) for filename in imageFilenames]
        for job in jobs:
            job.wait()

        try:
            results=OsRun(cmdline).run(maxWait=60) # time out if the program takes too long
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
            start and block until completion, terminate program if object is deleted (which is unlikely)
            use if you need the program to complete or its output before proceeding
        runAsync()->OsRunJob
            start in bg and move on with this thread, terminate program if object is deleted
            use if you need to do something else while the program is running
        detatch runAsync()->None
            run even if the object (or even the creator app) goes out of scope
            use for starting other applications that will out-live your own
        detatch run()
            Not allowed (doesn't make sense)
    """

    def __init__(self,
        cmd:typing.Union[str,typing.Iterable[str]],
        params:typing.Optional[typing.Iterable[str]]=None,
        shell:bool=False,
        detatch:bool=False,
        debug:bool=False,
        cmdLineSplit:typing.Optional[bool]=None,
        workingDirectory:typing.Optional[str]=None,
        env:typing.Optional[typing.Dict[str,typing.Any]]=None,
        callOnStdoutLine:typing.Optional[StringNotifies]=None,
        callOnStderrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutErrLine:typing.Optional[StringNotifies]=None,
        callOnStdoutChar:typing.Optional[StringNotifies]=None,
        callOnStderrChar:typing.Optional[StringNotifies]=None,
        callOnStdoutErrChar:typing.Optional[StringNotifies]=None,
        priority:int=MEDIUM_PRIORITY
        ):
        """
        :param workingDirectory: perform the operation in a specific directory
            * NOTE: there may be issues with multiple simultaneous programs
        :param cmdLineSplit: how and when to split cmd parameter
            if True will always attempt to split cmd into params
            if False will not
            if None (default) will only attempt if params[] is None
        """
        useParams:typing.List[str]=[]
        if cmd is not None and hasattr(cmd,'__iter__') and not isinstance(cmd,str):
            if not isinstance(cmd,(list,tuple)):
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
        if params is not None:
            useParams.extend(params)
        self.priority=priority
        self.params:typing.List[str]=useParams # params to pass to the command
        self.cmd:str=cmd # command to run
        self.shell:bool=shell # run in the system shell environment (slower and usually unnecessary)
        self.detatch:bool=detatch # detatch from this process/run in background
        self.debug:bool=debug # print the command input and output for debugging
        self.workingDirectory:typing.Optional[str]=workingDirectory
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
    
    def addCallOnStdoutLine(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        extendStringNotifies(self.callOnStdoutLine,addThis)
        
    def addCallOnStdoutChar(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        extendStringNotifies(self.callOnStdoutChar,addThis)
    
    def addCallOnStderrLine(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        extendStringNotifies(self.callOnStderrLine,addThis)
        
    def addCallOnStderrChar(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        extendStringNotifies(self.callOnStderrChar,addThis)
    
    def addCallOnStdoutErrLine(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new line of data
        """
        extendStringNotifies(self.callOnStdoutErrLine,addThis)
        
    def addCallOnStdoutErrChar(self,addThis:typing.Optional[StringNotifies]=None)->None:
        """
        add function(s) to call on new char of data
        """
        extendStringNotifies(self.callOnStdoutErrChar,addThis)

    @property
    def json(self)->str:
        return json.dumps(self.jsonObj)
    @json.setter
    def json(self,jsonString:typing.Union[str,bytes]):
        if isinstance(jsonString,bytes):
            jsonString=jsonString.decode('utf-8','ignore')
        self.jsonObj=json.loads(jsonString)

    @property
    def jsonObj(self)->typing.Dict[str,typing.Any]:
        ret:typing.Dict[str,typing.Any]={'cmd':self.cmd}
        if self.params:
            ret['params']=self.params
        if self.shell:
            ret['shell']=self.shell
        if self.detatch:
            ret['detatch']=self.detatch
        if self.debug:
            ret['debug']=self.debug
        if self.workingDirectory is not None and self.workingDirectory:
            ret['workingDirectory']=self.workingDirectory
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.cmd=jsonObj.get('cmd','')
        self.params=jsonObj.get('params',[])
        self.shell=jsonObj.get('shell',False)
        self.detatch=jsonObj.get('detatch',False)
        self.debug=jsonObj.get('debug',False)
        self.workingDirectory=jsonObj.get('workingDirectory',None)

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
        
    def __call__(self,moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None,maxWait:typing.Optional[float]=None)->OsRunResult:
        """
        shortcut for run()

        returns (returncode,stdout,stderr,stdouterr)
        """
        return self.run(moreParams,workingDirectory,maxWait)
    
    def run(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None,
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
        if self.detatch:
            raise Exception('For detatched process, only runAsync() is supported!')
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
        workingDirectory:typing.Optional[str]=None,
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
            errStr=str("ERR: job took longer than %s sec and was killed."%str(maxWait))
            ret=OsRunResult(-2400,'',errStr,errStr)
        if ret.failed:
            print(ret,file=sys.stderr)
        return ret

    def runAsync(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None,
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

    def runIterAllOutput(self,moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None)->typing.Generator[str,None,None]:
        """
        The idea is you run the command and get the lines back one at a time as an iterator

        for line in OsRun("ps -A").runIterAllOutput():
            ...

        NOTE: if you don't care about moreParams or maxWait, you can get even simpler
            for line in OsRun("ps -A"):
                ...
        """
        job=OsRunJob(self)
        it=job.outerrBuf.lineIter()
        job.start(moreParams,workingDirectory)
        yield from it
        
    def runIterStdout(self,moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None)->typing.Generator[str,None,None]:
        """
        The idea is you run the command and get the stdout lines back one at a time as an iterator

        for line in OsRun("ps -A").runIterStdout():
            ...

        NOTE: runIterAllOutput() gets both stdout and stderr mixed
        """
        job=OsRunJob(self)
        it=job.outBuf.lineIter()
        job.start(moreParams,workingDirectory)
        yield from it
        
    def runIterStderr(self,moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None)->typing.Generator[str,None,None]:
        """
        The idea is you run the command and get the stderr lines back one at a time as an iterator

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
    detatch:bool=False,
    debug:bool=False,
    cmdLineSplit:typing.Optional[bool]=None,
    workingDirectory:typing.Optional[str]=None,
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
        detatch,debug,
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
    printhelp=False
    shell=False
    detatch=False
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
                printhelp=True
            elif av[0]=='--shell':
                if len(av)<2:
                    shell=True
                else:
                    shell=av[1][0].lower() in ('1','t','y')
            elif av[0]=='--detatch':
                if len(av)<2:
                    detatch=True
                else:
                    detatch=av[1][0].lower() in ('1','t','y')
            elif av[0]=='--maxWait':
                if len(av)<2:
                    maxWait=None
                else:
                    maxWait=float(av[1])
            else:
                print('ERR: Unknown Argument "%s"'%arg)
                printhelp=True
        else:
            osr=OsRun(arg,shell=shell,detatch=detatch,debug=False)
            if useIter:
                for line in osr:
                    print(line)
            else:
                results=osr(maxWait=maxWait)
                print(results)
    if dashMode:
        osr=OsRun(dashModeCmd,dashModeArgs,shell=shell,detatch=detatch,debug=False)
        if useIter:
            for line in osr:
                print(line)
        else:
            results=osr(maxWait=maxWait)
            print(results)
    if printhelp:
        print('Useage:')
        print('   osrun.py [options] "[cmd params]" ...')
        print('Options:')
        print('   --help .............. show this help')
        print('   --shell ............. run with a shell environment')
        print('   --wmaxWait=sec ...... how long to wait for the program')
        print('   --detatch ........... run detatched from this console (closing console will not close program)')
        print('   - ................... everything after this point is cmd+params (convenience to not have to quote everything)')
        print('NOTE:')
        print('   files and options are evaluated IN ORDER')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))        