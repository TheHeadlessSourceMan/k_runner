"""
bit of an ease of use wrapper around subprocess.Popen()
"""
import typing
import os
import sys
from pathlib import Path
import json
from k_runner.dataRecievedCallbacks import DataRecievedCallbacks
from k_runner.processes import MEDIUM_PRIORITY
from k_runner.osRunResult import OsRunResult
from k_runner.osRunJob import OsRunJob
from k_runner.cmdline import CommandLineCompatible,CommandLine
from k_runner.environmentVariables import (
    EnvironmentVariablesCompatible,EnvironmentVariables)


class OsRun(DataRecievedCallbacks):
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
        commandLine:CommandLineCompatible,
        shell:bool=False,
        detach:bool=False,
        debug:bool=False,
        workingDirectory:typing.Union[None,str,Path]=None,
        environmentVariables:typing.Optional[
            EnvironmentVariablesCompatible]=None,
        runCallbacks:typing.Optional[DataRecievedCallbacks]=None,
        priority:float=MEDIUM_PRIORITY,
        ansiHandling:str="strip",
        showHidden:bool=False,
        showMinimized:bool=False,
        showMaximized:bool=False,
        env:typing.Optional[
            EnvironmentVariablesCompatible]=None # alias for compatability
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
        DataRecievedCallbacks.__init__(self,runCallbacks=runCallbacks)
        self.ansiHandling=ansiHandling
        useParams:typing.List[str]=[]
        self.priority=priority
        self.params:typing.List[str]=useParams # params to pass to the command
        self._commandLine:CommandLine=CommandLine(commandLine) # command to run
        self.shell:bool=shell # run in the system shell environment (slower and usually unnecessary) # noqa: E501 # pylint: disable=line-too-long
        self.detach:bool=detach # detach from this process/run in background
        self.debug:bool=debug # print the command input and output for debugging # noqa: E501 # pylint: disable=line-too-long
        self.workingDirectory:typing.Optional[Path]=None
        if workingDirectory is not None:
            self.workingDirectory=Path(str(workingDirectory)).absolute()
        if environmentVariables is None:
            if env is not None:
                environmentVariables=EnvironmentVariables(env)
            else:
                environmentVariables=EnvironmentVariables(os.environ)
        else:
            environmentVariables=EnvironmentVariables(environmentVariables)
        self._environmentVariables:EnvironmentVariables=environmentVariables
        self.showHidden=showHidden
        self.showMinimized=showMinimized
        self.showMaximized=showMaximized
        self.chunkyIO=False # read io in chunks instead of single bytes

    @property
    def environmentVariables(self)->EnvironmentVariables:
        """
        Environment variables
        """
        return self._environmentVariables
    @environmentVariables.setter
    def environmentVariables(self,env:EnvironmentVariablesCompatible):
        self._environmentVariables=EnvironmentVariables(env)
    @property
    def environ(self)->EnvironmentVariables:
        """
        Environment variables
        """
        return self.environmentVariables
    @environ.setter
    def environ(self,env:EnvironmentVariablesCompatible):
        self.environmentVariables=env
    @property
    def env(self)->EnvironmentVariables:
        """
        Environment variables
        """
        return self.environmentVariables
    @env.setter
    def env(self,env:EnvironmentVariablesCompatible):
        self.environmentVariables=env

    @property
    def commandLine(self)->CommandLine:
        """
        The command line for this program
        """
        return self._commandLine
    @commandLine.setter
    def commandLine(self,commandLine:CommandLineCompatible):
        self._commandLine=CommandLine(commandLine)
    @property
    def cmd(self)->CommandLine:
        """
        The command line for this program
        """
        return self.commandLine
    @cmd.setter
    def cmd(self,commandLine:CommandLineCompatible):
        self.commandLine=commandLine
    @property
    def cmdline(self)->CommandLine:
        """
        The command line for this program
        """
        return self.commandLine
    @cmdline.setter
    def cmdline(self,commandLine:CommandLineCompatible):
        self.commandLine=commandLine

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
        if self.environmentVariables:
            ret['environmentVariables']=self.environmentVariables.jsonObj
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.cmd=jsonObj.get('cmd','')
        self.params=jsonObj.get('params',[])
        self.shell=jsonObj.get('shell',False)
        self.detach=jsonObj.get('detach',False)
        self.debug=jsonObj.get('debug',False)
        env=jsonObj.get('environmentVariables')
        if env is not None:
            self.environmentVariables=EnvironmentVariables(env)
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
        runCallbacks:typing.Optional[DataRecievedCallbacks]=None,
        moreEnvironmentVariables:typing.Optional[
            EnvironmentVariablesCompatible]=None
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
            runCallbacks,
            moreEnvironmentVariables)
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
        runCallbacks:typing.Optional[DataRecievedCallbacks]=None,
        moreEnvironmentVariables:typing.Optional[
            EnvironmentVariablesCompatible]=None
        )->OsRunJob:
        """
        run the command asynchronously

        returns RunJob object representing the current job

        NOTE: if RunJob is garbage collected, the job itself will terminate
        """
        job=OsRunJob(self,runCallbacks=self)
        job.chunkyIO=self.chunkyIO
        job.extendCallbacks(runCallbacks)
        job.start(moreParams,workingDirectory,moreEnvironmentVariables)
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
        job.start(moreParams,workingDirectory)
        yield from job.lines

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
        job.start(moreParams,workingDirectory)
        yield from job.stdoutLines

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
        job.start(moreParams,workingDirectory)
        yield from job.stderrLines

    def __iter__(self)->typing.Iterator[str]:
        """
        shortcut for runIterAllOutput()
        """
        return self.runIterAllOutput()


def osrun(
    cmd:CommandLineCompatible,
    shell:bool=False,
    detach:bool=False,
    debug:bool=False,
    workingDirectory:typing.Union[None,str,Path]=None,
    environmentVariables:typing.Optional[
        EnvironmentVariablesCompatible]=None,
    runCallbacks:typing.Optional[DataRecievedCallbacks]=None,
    priority:float=MEDIUM_PRIORITY,
    ansiHandling:str="strip",
    showHidden:bool=False,
    showMinimized:bool=False,
    showMaximized:bool=False,
    env:typing.Optional[
        EnvironmentVariablesCompatible]=None # alias for compatability
    )->OsRunResult:
    """ shortcut for OsRun().run(...) """
    return OsRun(cmd,
        shell,
        detach,
        debug,
        workingDirectory,
        environmentVariables,
        runCallbacks,
        priority,
        ansiHandling,
        showHidden,
        showMinimized,
        showMaximized,
        env).run()
osRun=osrun
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
    dashModeArgs:typing.List[str]=[]
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
        args=[dashModeCmd]
        args.extend(dashModeArgs)
        osr=OsRun(
            args,
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
