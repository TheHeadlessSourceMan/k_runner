"""
Extension of osrun to filter the execution output
"""
import typing
import re
from k_runner.osrun import OsRun


class FilterRun:
    """
    Run something and filter the results as they come in
    """

    def __init__(self,cmd:str,params:typing.Optional[typing.Iterable[str]]=None,shell:bool=False,detatch:bool=False,
        debug:bool=False,cmdLineSplit:typing.Optional[bool]=None):
        """
        :param cmdLineSplit: how and when to split cmd parameter
            if True will always attempt to split cmd into params
            if False will not
            if None (default) will only attempt if params[] is None
        """
        self.osrun=OsRun(cmd,params,shell,detatch,debug,cmdLineSplit)
        self.filterOut:typing.List[typing.Pattern]=[]
        
    def addFilter(self,filter:typing.Union[str,typing.Pattern])->None:
        if isinstance(filter,str):
            filter=re.compile(filter)
        self.filterOut.append(filter)

    def checkFilters(self,line:str,filters:typing.Optional[typing.List[typing.Pattern]]=None):
        """
        returns True if it matches any of the given filters
        """
        if filters is None:
            filters=self.filterOut
        for filter in filters:
            if filter.match(line) is not None:
                return True
        return False

    def runIter(self)->typing.Generator[str,None,None]:
        """
        run the program and yeild only lines that 
        """
        for line in self.osrun:
            if not self.checkFilters(line,self.filterOut):
                yield line

    def __iter__(self)->typing.Iterator[str]:
        return self.runIter()


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
            osr=FilterRun(arg,shell=shell,detatch=detatch,debug=False)
            if useIter:
                for line in osr:
                    print(line)
            else:
                results=osr(maxWait=maxWait)
                print(results)
    if dashMode:
        osr=FilterRun(dashModeCmd,dashModeArgs,shell=shell,detatch=detatch,debug=False)
        if useIter:
            for line in osr:
                print(line)
        else:
            results=osr(maxWait=maxWait)
            print(results)
    if printhelp:
        print('Useage:')
        print('   filterRun.py [options] "[cmd params]" ...')
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