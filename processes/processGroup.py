"""
A group of processes
"""
import typing
from pathlib import Path
from .process import Process
from .asProcess import ProcessCompatible,asProcess
if typing.TYPE_CHECKING:
    from k_runner.ui.window import Window

class ProcessGroup:
    """
    A group of processes
    """
    def __init__(self,
        processes:typing.Union[None,
            ProcessCompatible,
            typing.Iterable[ProcessCompatible]]=None):
        """ """
        self._procs:typing.Set[Process]=set[Process]()
        if processes is not None:
            self.append(processes)

    def watchProcessesEnd(self,
        fn:typing.Optional[typing.Callable[[Process],None]]=None,
        pollingInterval:float=0.5
        )->None:
        """
        Watch for processes when they end.

        Generally, you'd want to do:
            threading.Thread(target=watchProcessEnd,args=(my_function,).start()

        This removes processes from the group as they disappear.
        It then keeps running until all of the group is empty.

        Therefore, you could also use it to wait for everything to end like:
            watchProcessEnd(None)
        """
        import time
        while self._procs:
            time.sleep(pollingInterval)
            for process in self._procs:
                if not process.is_running():
                    if fn is not None:
                        fn(process)
                    self._procs.remove(process)

    def dropEndedProcesses(self)->typing.Iterable[Process]:
        """
        Get rid of processes in the list that have ended.

        Returns a list of them in case you want to see what closed.
        """
        ret=[]
        for process in self._procs:
            if not process.is_running():
                ret.append(process)
        for process in ret:
            self._procs.remove(process)
        return ret
    dropClosedProcesses=dropEndedProcesses

    def setPriority(self,priority:float)->None:
        """
        Set the process priority as a percent
        where 1.0 is the max priority of 100%
        """
        for process in self._procs:
            process.setPriority(priority)

    def increasePriority(self,byAmount:float=0.475)->None:
        """
        Increase the process priority percent
        """
        for process in self._procs:
            process.increasePriority(byAmount)

    def decreasePriority(self,byAmount:float=0.475)->None:
        """
        Decrease the process priority percent
        """
        for process in self._procs:
            process.decreasePriority(byAmount)

    def filtered(self,
        processName:typing.Union[None,str,typing.Pattern]=None,
        cmdline:typing.Union[None,
            str,Path,typing.Pattern,typing.Iterable[str],Process]=None,
        hasNetworkPortOpen:
            typing.Union[None,int,typing.Iterable[int],bool]=None,
        hasFileOpen:typing.Union[
            None,str,Path,typing.Iterable[typing.Union[str,Path]]]=None,
        isRunning:typing.Optional[bool]=True
        )->typing.Generator[Process,None,None]:
        """
        Get a filtered group
        """
        for process in self._procs:
            # check that the process is still running
            if isRunning is not None:
                if isRunning!=process.is_running():
                    continue
            # check that the name matches
            if processName is not None:
                if isinstance(processName,str):
                    if processName.lower() not in process.name:
                        continue
                elif processName.match(process.name) is None:
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
            yield process

    def kill(self)->None:
        """
        KILL THEM ALL!!!
        """
        for process in self._procs:
            process.kill()

    def cpu_percent(self,
        interval:typing.Optional[float]=None
        )->float:
        """
        Total CPU percent for the entire group
        """
        total=0.0
        for process in self._procs:
            pct=process.cpu_percent(interval)
            if isinstance(pct,float):
                total+=pct
        return total

    def getHwnds(self,visibleOnly:bool=True)->typing.Iterable[int]:
        """
        Get the window handles associated with the processes
        """
        for process in self._procs:
            yield from process.getHwnds(visibleOnly)

    @property
    def hwnds(self)->typing.Iterable[int]:
        """
        Get the window handles associated with the processes
        """
        return self.getHwnds()

    def getWindows(self)->typing.Iterable["Window"]:
        """
        Get all top level windows for the process
        """
        for process in self._procs:
            yield from process.getWindows()
    @property
    def windows(self)->typing.Iterable["Window"]:
        """
        Get all top level windows for the process
        """
        return self.getWindows()

    def makeForeground(self)->None:
        """
        Bring all associated windows to the top

        NOTE: Be a good citizen and use this sparingly!
        """
        for process in self._procs:
            process.makeForeground()
    bringToFront=makeForeground
    makeWindowForeground=makeForeground

    def setMinimized(self,minimize:bool=True)->None:
        """
        Minimize all windows
        """
        for process in self._procs:
            process.minimize(minimize)
    minimize=setMinimized

    def setMaximized(self,maximize:bool=True)->None:
        """
        Maximize all windows
        """
        for process in self._procs:
            process.setMaximized(maximize)
    maximize=setMaximized

    def restore(self)->None:
        """
        Restore all windows
        """
        for process in self._procs:
            process.restore()

    def append(self,
        processes:typing.Union[None,
            ProcessCompatible,typing.Iterable[ProcessCompatible]]=None
        )->None:
        """
        Add more processes to the list
        """
        if processes is None:
            return
        if not hasattr(processes,'__iter__'):
            processes=typing.cast(ProcessCompatible,processes)
            processes=(processes,)
        typing.cast(typing.Iterable[ProcessCompatible],processes)
        self._procs=self._procs.union([asProcess(p) for p in processes]) # type: ignore
    add=append
    extend=append

    def __iter__(self)->typing.Iterator[Process]:
        return iter(self._procs)

    def __repr__(self)->str:
        return '\n'.join([repr(p) for p in self._procs])
