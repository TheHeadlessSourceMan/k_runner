import threading
import time
import typing
from k_runner import (
    CommandLineCompatible,OsRunJob,Process,asCommandLine,getAllProcesses)


ProcessWatcherCallback=typing.Callable[['ProcessWatcher',Process],None]


class ProcessWatcher:
    def __init__(self,
        commandLine:CommandLineCompatible,
        startExclusive:bool=False,
        minRequired:int=0,
        maxAllowed:typing.Optional[int]=None,
        onProcessStarted:typing.Optional[ProcessWatcherCallback]=None,
        onProcessStopped:typing.Optional[ProcessWatcherCallback]=None):
        """
        Initialize the ProcessWatcher.

        :commandLine: The command line to watch.
        :startExclusive: Whether to start a new process exclusively for
            this watcher.  (Will shut down on object deletion.)
        :minRequired: The minimum number of required instances.
            (will automatically start new instances if below this number.)
        :maxAllowed: The maximum number of allowed instances.
            (will automatically stop instances if above this number.)
        :onProcessStarted: Callback when the process starts.
        :onProcessStopped: Callback when the process stops.
        """
        self.commandLine=asCommandLine(commandLine)
        self.minRequired=minRequired
        self.maxAllowed=maxAllowed
        self.onProcessStarted=onProcessStarted
        self.onProcessStopped=onProcessStopped
        self._currentProcesses:typing.List[Process]=[]
        self._exclusiveInstance:typing.Optional[OsRunJob]=None
        if startExclusive:
            self._exclusiveInstance=self.startExclusiveInstance()
        self.checkNow()

    def __del__(self):
        self.stopExclusiveInstance()

    def stopExclusiveInstance(self)->None:
        """
        Close the exclusive instance if one is running.
        """
        if self._exclusiveInstance is not None:
            self._exclusiveInstance.terminate()
            if self.onProcessStopped:
                self.onProcessStopped(self,self._exclusiveInstance)
            self._exclusiveInstance=None

    def startExclusiveInstance(self)->typing.Optional[OsRunJob]:
        """
        Start a new exclusive instance if not already running.
        """
        if self._exclusiveInstance is None:
            self._exclusiveInstance=self.commandLine.runAsync()
            if self.onProcessStarted:
                self.onProcessStarted(self,self._exclusiveInstance)
        return self._exclusiveInstance

    def restartExclusiveInstance(self)->typing.Optional[OsRunJob]:
        """
        Restart the exclusive instance.
        """
        self.stopExclusiveInstance()
        return self.startExclusiveInstance()

    @property
    def numInstances(self)->int:
        return len(self._currentProcesses)

    @property
    def isRunning(self)->bool:
        return len(self._currentProcesses)>0

    def checkNow(self,
        processList:typing.Optional[
            typing.Iterable[Process]]=None
        )->None:
        """
        Check the status of the process.
        """
        if processList is None:
            processList=getAllProcesses()
        validProcesses:typing.List[Process]=[]
        for p in processList:
            if p.commandLine==self.commandLine:
                validProcesses.append(p)
        # find added processes (do not add to list yet for efficiency)
        addedProcesses:typing.List[Process]=[]
        for p in validProcesses:
            if p not in self._currentProcesses:
                addedProcesses.append(p)
                if self.onProcessStarted:
                    self.onProcessStarted(self,p)
        # find removed processes
        for lastKnownProcess in self._currentProcesses[:]:
            if lastKnownProcess not in validProcesses:
                self._currentProcesses.remove(lastKnownProcess)
                if self.onProcessStopped:
                    self.onProcessStopped(self,lastKnownProcess)
        # add the added processes
        if addedProcesses:
            self._currentProcesses.extend(addedProcesses)
        # start anything that needs starting
        while len(self._currentProcesses)<self.minRequired:
            job=self.commandLine.runAsync()
            self._currentProcesses.append(job)
            if self.onProcessStarted:
                self.onProcessStarted(self,job)
        # stop anything that needs stopping
        if self.maxAllowed is not None:
            while len(self._currentProcesses)>self.maxAllowed:
                process=self._currentProcesses.pop()
                process.terminate()
                if self.onProcessStopped:
                    self.onProcessStopped(self,process)


class ProcessWatchers:
    """
    Manages a collection of ProcessWatcher instances
    and periodically checks their status.
    """
    def __init__(self,pollingInterval:float=0.5):
        self.pollingInterval=pollingInterval
        self._watchers:typing.List[ProcessWatcher]=[]
        self._keepgoing:bool=True
        self._thread:typing.Optional[threading.Thread]=None

    def __iter__(self)->typing.Iterator[ProcessWatcher]:
        return iter(self._watchers)

    def addWatchers(self,
        watcher:typing.Union[ProcessWatcher,typing.Iterable[ProcessWatcher]]
        )->None:
        """
        Add one or more new ProcessWatcher to the collection.

        Args:
            watcher (ProcessWatcher): The watcher to add.
        """
        if isinstance(watcher, ProcessWatcher):
            self._watchers.append(watcher)
        else:
            self._watchers.extend(watcher)
    addWatcher=addWatchers
    append=addWatchers
    add=addWatchers
    extend=addWatchers

    def _threadLoop(self):
        """
        Loop that continuously checks the
        status of all registered process watchers.
        """
        # main loop
        while self._keepgoing:
            processList=list(getAllProcesses())
            for watcher in self._watchers:
                watcher.checkNow(processList)
            time.sleep(self.pollingInterval)

    def start(self)->threading.Thread:
        """
        Start the background thread that monitors all
        registered process watchers.

        Returns:
            threading.Thread: The thread object running the monitoring loop.
        """
        self._keepgoing=True
        self._thread=threading.Thread(target=self._threadLoop,daemon=True)
        self._thread.start()
        return self._thread

    def stop(self):
        """
        Stop the background thread that monitors all
        registered process watchers.
        """
        self._keepgoing=False
        while self._thread is not None:
            self._keepgoing=False
            self._thread.join(0.5)
            self._thread=None

    def wait(self):
        """
        Wait for the background thread to finish.
        """
        while self._thread is not None:
            time.sleep(0.25)


def cmdline(args:typing.List[str])->int:
    """
    Run like a command line
    """
    cmdline:typing.List[str]=[]
    gettingCommandLine=False
    printHelp=False
    startExclusive:bool=False
    minRequired:int=0
    maxAllowed:typing.Optional[int]=None
    pollingInterval:float=0.25
    for arg in args:
        if gettingCommandLine:
            cmdline.append(arg)
            continue
        elif arg.startswith('-'):
            kv=arg.split('=',1)
            if arg in ("-h","--help"):
                printHelp=True
                break
            elif arg in ("-","--"):
                gettingCommandLine=True
                continue
            elif kv[0].lower()=="--startexclusive":
                if len(kv)<2:
                    startExclusive=True
                else:
                    startExclusive=kv[1][0].lower() in ("1","t","y")
            elif kv[0].lower()=="--minrequired":
                if len(kv)<2:
                    minRequired=1
                else:
                    minRequired=int(kv[1])
            elif kv[0].lower()=="--maxallowed":
                if len(kv)<2:
                    maxAllowed=None
                else:
                    maxAllowed=int(kv[1])
            elif kv[0].lower()=="--pollinginterval":
                if len(kv)<2:
                    pollingInterval=0.25
                else:
                    pollingInterval=float(kv[1])
            else:
                print(f"Unknown argument: {arg}")
                printHelp=True
                break
        else:
            try:
                n=int(arg)
                minRequired=n
            except ValueError:
                print(f"Unknown argument: {arg}")
                printHelp=True
                break
    if not cmdline:
        print("No command line specified")
        printHelp=True
    else:
        def onProcessStarted(w:ProcessWatcher,process:Process):
            print(f"Process started: {process}")
        def onProcessStopped(w:ProcessWatcher,process:Process):
            print(f"Process stopped: {process}")
        pw=ProcessWatchers(pollingInterval)
        w=ProcessWatcher(cmdline,
            startExclusive,
            minRequired,
            maxAllowed,
            onProcessStarted,
            onProcessStopped)
        pw.append(w)
        pw.start()
        pw.wait()
    if printHelp:
        print("Usage: processWatcher.py [options] -- command line to execute")
        print("Options:")
        print("  -h, --help ......... Show this help message and exit")
        print("  --startExclusive ... Start the process exclusively")
        print("  --minRequired ...... Minimum number of required processes")
        print("          NOTE: you can specify this number without --minRequired=") # noqa: E501
        print("  --maxAllowed ....... Maximum number of allowed processes")
        print("  --pollingInterval .. Polling interval for checking process status") # noqa: E501
        return -1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(cmdline(sys.argv[1:]))
