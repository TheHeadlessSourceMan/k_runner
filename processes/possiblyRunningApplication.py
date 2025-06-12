"""
Tools to check if a process is running, and if so,
stop it, do something, then restart it.
"""
import typing
from collections.abc import Iterable
import os
from pathlib import Path
import subprocess
import psutil


AppRestartType=typing.List[typing.Tuple[str,typing.List[str]]]


class PossiblyRunningApplication:
    """
    When a compile fails because it cannot write to a given file
    because an application is already running.

    When this happens, this class can halt the offending application,
    then you can compile, then this can restart it
    """
    def __init__(self,
        application:typing.Union[str,Path],
        alsoLocks:typing.Optional[typing.Iterable[
            typing.Union[str,Path]]]=None):
        """
        :application: the application we are talking about
        :alsoLocks: in addition to the application itself, it can lock
            these other files as well (for example, if the app is using a dll)
        """
        if not isinstance(application,Path):
            application=Path(application)
        self.application:Path=application
        self.alsoLocks:typing.List[Path]=[]
        if alsoLocks is not None:
            for f in alsoLocks:
                if not isinstance(f,Path):
                    f=Path(f)
                self.alsoLocks.append(f.absolute())
        self._stuffThatWeStopped:AppRestartType=[] # remember the app(s)

    def __equ__(self,otherFilename:str)->bool:
        return self.doesItLock(otherFilename)

    def doesItLock(self,otherFilename:typing.Union[str,Path])->bool:
        """
        When compiler says "cannot write to 'foo.exe'", you can use this to
        test if this PossiblyRunningApplication can stop a running application
        and free up the lock,
        """
        if not isinstance(otherFilename,Path):
            otherFilename=Path(otherFilename)
        otherFilename=otherFilename.absolute()
        filename=self.application
        if os.sep=='\\':
            # windows filenames are not case-sensitive
            otherFilename=otherFilename.lower()
            filename=filename.lower()
        if otherFilename.endswith(filename):
            return True
        for filename in self.alsoLocks:
            if os.sep=='\\':
                filename=filename.lower()
            if filename==otherFilename:
                return True
        return False

    def stop(self)->int:
        """
        stop all instances of the application, storing info on
        everything stopped to self._stuffThatWeStopped
        """
        self._stuffThatWeStopped=[]
        filename=self.application
        if os.sep=='\\':
            # windows filenames are not case-sensitive
            filename=filename.lower()
        for proc in psutil.process_iter(['name', 'exe', 'cmdline']):
            processFullFilename=proc.info['exe']
            if processFullFilename is None or not processFullFilename:
                continue
            if os.sep=='\\':
                # windows filenames are not case-sensitive
                processFullFilename=processFullFilename.lower()
            if processFullFilename.endswith(filename):
                processArgs=proc.info['cmdline']
                # make the args a proper argv, including full path in filename
                if processArgs is None or len(processArgs)<1:
                    processArgs=[processFullFilename]
                else:
                    processArgs[0]=processFullFilename
                pid=proc.pid
                try:
                    print(f'killing ({pid}): {argvToString(processArgs)}')
                    self._stuffThatWeStopped.append(
                        (processFullFilename,processArgs))
                    proc.kill()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
        return len(self._stuffThatWeStopped)

    def start(self)->None:
        """
        restart the applications we stop()'ed
        """
        for _,argv in self._stuffThatWeStopped:
            print(f'restarting: {argvToString(argv)}')
            subprocess.Popen(argv,shell=True,stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


def stopAllProcesses(application:str)->int:
    """
    Stop all processes that match a given application name()
    """
    px=PossiblyRunningApplication(application)
    return px.stop()
kill=stopAllProcesses


def temporarilyStopAllProcesses(
    application:str,
    runBeforeRestarting:typing.Union[typing.Callable,str,typing.Iterable[str]]
    )->typing.Any:
    """
    :runBeforeRestarting: can be a python function, or one
        or more strings representing command line arguments

    This:
        1) stops all instances of a given process
        2) runs the provided function
        3) restarts all of the stopped instances

    NOTE: still will restart programs, even if runBeforeRestarting generates
        an exception
    """
    runFnException=None
    result=None
    px=PossiblyRunningApplication(application)
    px.stop()
    if callable(runBeforeRestarting):
        try:
            result=typing.cast(typing.Callable,runBeforeRestarting)()
        except Exception as e:
            runFnException=e
    else:
        if isinstance(runBeforeRestarting,str):
            runBeforeRestarting=[runBeforeRestarting]
        elif not isinstance(runBeforeRestarting,Iterable):
            runBeforeRestarting=[x for x in runBeforeRestarting]
        try:
            po=subprocess.Popen(runBeforeRestarting,
                shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            result,_=po.communicate()
            result=result.decode('utf-8')
        except Exception as e:
            runFnException=e
    px.start()
    if runFnException:
        raise runFnException
    return result


def cmdline(args:typing.Iterable[str])->int:
    """
    Call this with command line parameters
    (WITHOUT the filename as the first argument)
    """
    printhelp=False
    stop=None
    temporarilyStop=None
    stray=[]
    dashMode=False
    dashModeArgv=[]
    # process the supplied args
    for arg in args:
        if dashMode:
            dashModeArgv.append(arg)
        elif arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-','--'):
                dashMode=True
            elif av[0] in ('-h','--help','/?'):
                printhelp=True
            elif av[0] in ('--stop','--stopallprocesses','--kill'):
                if len(av)<2 or not av[1]:
                    print('ERR: need a program name to stop')
                    printhelp=True
                else:
                    stop=av[0]
            elif av[0] in ('--temporarilystop',
                '--temporarilystopallprocesses'):
                if len(av)<2 or not av[1]:
                    print('ERR: need a program name to temporarliy stop')
                    printhelp=True
                else:
                    temporarilyStop=av[1]
            else:
                stray.append(arg)
        else:
            stray.append(arg)
    # do whatever they asked
    if not printhelp:
        if temporarilyStop is not None:
            if not dashMode:
                print('ERR: expected command to end in "- shellcmd"')
                printhelp=True
            else:
                ret=temporarilyStopAllProcesses(temporarilyStop,dashModeArgv)
                print(ret)
        elif stop is not None:
            stopAllProcesses(stop)
        elif stray:
            strayStr=' '.join(stray)
            if dashMode:
                ret=temporarilyStopAllProcesses(strayStr,dashModeArgv)
                print(ret)
            else:
                stopAllProcesses(strayStr)
        else:
            print('ERR: need to specify a command')
            printhelp=True
    # if it can't be done, print the help table
    if printhelp:
        print('Useage:')
        print('   possiblyRunningApplication.py [commands] ...')
        print('Commands:')
        print('   --stop=exefilename .............. stop running instances')
        print('         of this file')
        print('         also: --stopAllProcess and --kill do the same thing')
        print('   --temporarilyStop=exefilename ... stop all instances ofs')
        print('         exeFilename, run command after "-", then restart them')
        print('         also: --temporarilyStopAllProcess does the same thing')
        print('   - ................... everything after this point iss')
        print('         cmd+params to be called when doing --temporarilyStop')
        print('         also: -- does the same thing')
        print('NOTE:')
        print('   as a shortcut, if just an exefilename is specified, it will')
        print('         determine whether to --stop or --temporarlyStop')
        print('   eg')
        print('        possiblyRunningApplication.py')
        print('            --temporarlyStop=foo.exe -- ls -la')
        print('   is the same as')
        print('        possiblyRunningApplication.py foo.exe -- ls -la')
        print('   and')
        print('        possiblyRunningApplication.py --stop=foo.exe')
        print('   is the same as')
        print('        possiblyRunningApplication.py foo.exe')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
