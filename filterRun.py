"""
Extension of osrun to filter the execution output
"""
import typing
import re
from .cmdline.asCommandLine import CommandLineCompatible
from .cmdline.commandLine import CommandLine
from .osrun import OsRun


class FilterRun:
    """
    Run something and filter the results as they come in
    """

    def __init__(self,
        cmd:CommandLineCompatible,
        shell:bool=False,
        detach:bool=False,
        debug:bool=False):
        """ """
        self.osrun=OsRun(cmd,shell,detach,debug)
        self.filterOut:typing.List[typing.Pattern[str]]=[]

    def addFilter(self,
        flt:typing.Union[str,typing.Pattern[str]],
        compileFlags:int=0
        )->None:
        """
        add another filter to the list of filters
        """
        if isinstance(flt,str):
            flt=re.compile(flt,compileFlags)
        self.filterOut.append(flt)

    def checkFilters(self,
        line:str,
        filters:typing.Optional[typing.List[typing.Pattern[str]]]=None
        )->bool:
        """
        returns True if it matches any of the given filters
        """
        if filters is None:
            filters=self.filterOut
        for flt in filters:
            if flt.match(line) is not None:
                return True
        return False

    def runIter(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None,
        maxWait:typing.Optional[float]=None
        )->typing.Generator[str,None,None]:
        """
        run the program and yield only lines that
        are not filtered out by the filters
        """
        for line in self.osrun(
            moreParams,
            workingDirectory,
            maxWait):
            #
            if not self.checkFilters(line,self.filterOut):
                yield line

    def __call__(self,
        moreParams:typing.Optional[typing.Iterable[str]]=None,
        workingDirectory:typing.Optional[str]=None,
        maxWait:typing.Optional[float]=None
        )->typing.Generator[str,None,None]:
        """
        run the program and yield only lines that
        are not filtered out by the filters
        """
        return self.runIter(
            moreParams,
            workingDirectory,
            maxWait)

    def __iter__(self)->typing.Iterator[str]:
        return self.runIter()


def cmdline(args:typing.Iterable[str])->int:
    """
    Call this module with command line arguments array
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
            osr=FilterRun(arg,shell=shell,detach=detach,debug=False)
            if useIter:
                for line in osr:
                    print(line)
            else:
                results=osr(maxWait=maxWait)
                print(results)
    if dashMode:
        cmd=CommandLine(dashModeCmd)
        cmd.extend(dashModeArgs)
        osr=FilterRun(cmd,shell=shell,detach=detach,debug=False)
        if useIter:
            for line in osr:
                print(line)
        else:
            results=osr(maxWait=maxWait)
            print(results)
    if printHelp:
        print('Usage:')
        print('   filterRun.py [options] "[cmd params]" ...')
        print('Options:')
        print('   --help .......... show this help')
        print('   --shell ......... run with a shell environment')
        print('   --maxWait=sec ... how long to wait for the program')
        print('   --detach ........ run detached from this console')
        print('                (closing console will not close program)')
        print('   - ............... everything after this point is cmd+params')
        print('                (convenience to not have to quote everything)')
        print('NOTE:')
        print('   files and options are evaluated IN ORDER')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
