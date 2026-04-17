"""
Special case of a process that is dealing with a script
"""
import typing
from pathlib import Path
from .process import Process
from .find import allSystemProcesses


class InterpreterProcess(Process):
    """
    A special-case process for an interpreted application

    This mainly adjusts the command line and things
    derived from it to account for the interpreter, for 
    instance, if the command line is ["python","foo.py","--name=kevin"]
    it acts like the program name was "foo.py" and its command
    line is ["foo.py","--name=kevin"]

    NOTE: if you want to get bak to the original command line,
        simply use interpretedProcess.interpreterProcess.commandLine
    """
    def __init__(self,
        interpretedAppType:"InterpretedAppType",
        interpreterProcess:Process):
        """ """
        self._interpretedAppType=interpretedAppType
        self._interpreterProcess=interpreterProcess
        Process.__init__(self,interpreterProcess.pid)

    @property
    def commandLine(self # type: ignore
        )->typing.List[str]:
        """
        Get the command line for the application
        """
        return list(self.interpreterProcess.commandLine)[1:]

    @property
    def interpreterProcess(self)->Process:
        """
        Get the process of the scripting app
        """
        return self._interpreterProcess

    @property
    def interpretedAppType(self)->"InterpretedAppType":
        """
        Type of scripting language we are looking at
        """
        return self._interpretedAppType
ScriptProcess=InterpreterProcess


class InterpretedAppType:
    """
    Special case of a process that is dealing with an interpreted
    app running through an interpreter program

    This replaces process name and file location with the interpreted
    app name, not the interpreter name.  For instance, instead
    of returning "python", it returns "foo.py"
    """
    def __init__(self,name:str,interpreterApplications:typing.Iterable[str]):
        self.name=name
        self.interpreterApplications=list(interpreterApplications)

    def __eq__(self,other):
        other=str(other).lower()
        return other==self.name or other in self.interpreterApplications

    def __repr__(self):
        return self.name


InterpretedAppTypes=[
    InterpretedAppType('python',['python','python3'])]


def findSystemProcessesSmart(
    processName:typing.Union[None,str,typing.Pattern[str],Process]=None,
    cmdline:typing.Union[None,
        str,Path,typing.Pattern[str],typing.Iterable[str],Process]=None,
    hasNetworkPortOpen:typing.Union[None,int,typing.Iterable[int],bool]=None,
    hasFileOpen:typing.Union[
        None,str,Path,typing.Iterable[typing.Union[str,Path]]]=None,
    isScriptAppType:typing.Union[None,InterpretedAppType,str]=None
    )->typing.Iterable[Process]:
    """
    Find all system processes that match, plus account
    for interpreted language processes.

    For instance in findSystemProcess() if you wanted to filter for
    processName="foo.py" you have a problem because the process name
    is "python", not "foo.py".  This will account for all that.
    """
    quickfind={}
    for typ in InterpretedAppTypes:
        for appName in typ.interpreterApplications:
            quickfind[appName]=typ
    for process in allSystemProcesses():
        typ=quickfind.get(process.commandLine[0])
        if isScriptAppType is not None:
            if typ!=isScriptAppType:
                continue
        if typ is not None:
            process=InterpreterProcess(typ,process)
        # match the process name
        if processName is not None:
            if not process.processNameMatches(processName):
                continue
        # match the command line
        if cmdline is not None:
            if not process.cmdlineMatches(cmdline):
                continue
        # match by network port
        if hasNetworkPortOpen is not None:
            if not process.hasNetworkPortOpen(hasNetworkPortOpen):
                continue
        # match by file
        if hasFileOpen is not None:
            if not process.hasFileOpen(hasFileOpen):
                continue
        # Looks good!
        yield process
