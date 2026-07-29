"""
Module for executing commands on multiple files concurrently using threads.
"""
import typing
from threading import Thread
from queue import Queue
from paths import Path, Url, UrlListCompatible,asUrlList
from k_runner import (
    MEDIUM_PRIORITY,CommandLine,CommandLineCompatible,
    DataRecievedCallbacks,EnvironmentVariables,EnvironmentVariablesCompatible,
    OsRunResult,asCommandLine,asEnvironmentVariables)


class ExecuteOnMultipleFiles:
    """
    Execute a command on multiple files concurrently.
    """
    def __init__(self,
        commandLine:CommandLineCompatible,
        files:typing.Optional[UrlListCompatible]=None,
        allowDuplicates:bool=False,
        numThreads:int=10,
        fileEnvKey:str='FILE',
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
        """
        self._commandLine:CommandLine=asCommandLine(commandLine)
        self.allowDuplicates=allowDuplicates
        self._addedFiles:typing.Set[Url]=set()
        self._fileQueue:Queue[Url]=Queue()
        self.fileEnvKey:str=fileEnvKey
        self.resultsQueue:Queue[typing.Tuple[Url,OsRunResult]]=Queue()
        self.numThreads=numThreads
        self.doneAdding=False
        self._threads:typing.List[Thread]=[]
        self.shell=shell
        self.detach=detach
        self.debug=debug
        self.workingDirectory=workingDirectory
        if environmentVariables is None:
            environmentVariables={}
        self.environmentVariables=asEnvironmentVariables(environmentVariables)
        if env is not None:
            self.environmentVariables.union(asEnvironmentVariables(env))
        self.runCallbacks=runCallbacks
        self.priority=priority
        self.ansiHandling=ansiHandling
        self.showHidden=showHidden
        self.showMinimized=showMinimized
        self.showMaximized=showMaximized
        self.add(files)

    @property
    def env(self)->EnvironmentVariables:
        """
        Same as environmentVariables
        """
        return self.environmentVariables

    @property
    def commandLine(self)->CommandLine:
        """
        The command line object.
        """
        return self._commandLine
    @commandLine.setter
    def commandLine(self,value:CommandLineCompatible):
        self._commandLine=asCommandLine(value)

    def add(self,
        files:typing.Optional[UrlListCompatible]=None
        )->None:
        """
        Add one or more files to the execution queue.

        :files: Files to add.
        """
        if files is None:
            return
        for f in asUrlList(files):
            f=f.absolute()
            if self.allowDuplicates or f not in self._addedFiles:
                self._addedFiles.add(f)
                self._fileQueue.put(f)
    append=add
    extend=add

    def _run1(self,file:Url)->OsRunResult:
        """
        Execute the command on a single file.

        :file: The file to execute the command on.
        """
        env=self.environmentVariables.copy()
        env[self.fileEnvKey]=str(file)
        result=self._commandLine.run(
            shell=self.shell,
            detach=self.detach,
            debug=self.debug,
            workingDirectory=self.workingDirectory,
            environmentVariables=env,
            runCallbacks=self.runCallbacks,
            priority=self.priority,
            ansiHandling=self.ansiHandling,
            showHidden=self.showHidden,
            showMinimized=self.showMinimized,
            showMaximized=self.showMaximized)
        self.resultsQueue.put((file,result))
        return result

    def _runLoop(self)->None:
        """
        Execute the command on all files in the queue.
        """
        while not self.doneAdding:
            while not self._fileQueue.empty():
                self._run1(self._fileQueue.get())

    def start(self)->None:
        """
        Execute the command on all files using multiple threads.
        """
        if self._threads:
            return
        self.doneAdding=False
        self._threads=[]
        for _ in range(self.numThreads):
            t=Thread(target=self._runLoop)
            t.start()
            self._threads.append(t)

    def wait(self)->typing.List[typing.Tuple[Url,OsRunResult]]:
        """
        Wait for all threads to complete and collect all results.

        :return: A list of tuples containing
        the file and its execution result.
        """
        self.doneAdding=True
        for t in self._threads:
            t.join()
        results:typing.List[typing.Tuple[Url,OsRunResult]]=[]
        while not self.resultsQueue.empty():
            results.append(self.resultsQueue.get())
        return results

    def run(self)->typing.List[typing.Tuple[Url,OsRunResult]]:
        """
        Execute the command on all files in parallel
        using multiple threads, wait for completion,
        and then return all results.
        """
        self.start()
        return self.wait()
    __call__=run
MultiExecute=ExecuteOnMultipleFiles

def cmdline(args:typing.List[str])->int:
    """
    Run like a command line
    """
    from paths import findFiles
    printHelp=False
    cmdline:typing.List[str]=[]
    files:typing.List[Path]=[]
    gettingCommandLine=False
    allowDuplicates:bool=False
    numThreads:int=10
    fileEnvKey:str='FILE'
    shell:bool=False
    detach:bool=False
    debug:bool=False
    workingDirectory:typing.Union[None,str,Path]=None
    environmentVariables:EnvironmentVariablesCompatible={}
    runCallbacks:typing.Optional[DataRecievedCallbacks]=None
    priority:float=MEDIUM_PRIORITY
    ansiHandling:str="strip"
    showHidden:bool=False
    showMinimized:bool=False
    showMaximized:bool=False
    recursive:bool=False
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
            elif kv[0].lower() in ('--recursive','-r'):
                if len(kv)<2:
                    recursive=True
                else:
                    recursive=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--allowduplicates',):
                if len(kv)<2:
                    allowDuplicates=True
                else:
                    allowDuplicates=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--numthreads',):
                if len(kv)<2:
                    numThreads=10
                else:
                    numThreads=int(kv[1])
            elif kv[0].lower() in ('--fileenvkey',):
                if len(kv)<2:
                    fileEnvKey='FILE'
                else:
                    fileEnvKey=kv[1]
            elif kv[0].lower() in ('--shell',):
                if len(kv)<2:
                    shell=True
                else:
                    shell=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--detach',):
                if len(kv)<2:
                    detach=True
                else:
                    detach=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--debug',):
                if len(kv)<2:
                    debug=True
                else:
                    debug=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--workingdirectory','--cwd'):
                if len(kv)<2:
                    workingDirectory=None
                else:
                    workingDirectory=kv[1]
            elif kv[0].lower() in ('--priority',):
                if len(kv)<2:
                    priority=0.5
                else:
                    priority=float(kv[1])
            elif kv[0].lower() in ('--ansi',):
                if len(kv)<2:
                    ansiHandling='strip'
                else:
                    ansiHandling=kv[1]
            elif kv[0].lower() in ('--showhidden',):
                if len(kv)<2:
                    showHidden=True
                else:
                    showHidden=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--showminimized',):
                if len(kv)<2:
                    showMinimized=True
                else:
                    showMinimized=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--showmaximized',):
                if len(kv)<2:
                    showMaximized=True
                else:
                    showMaximized=kv[1][0].lower() in ('1','t','y')
            elif kv[0].lower() in ('--env','--environmentvariables'):
                if len(kv)>1:
                    environmentVariables.update(
                        dict(item.split('=', 1)
                        for item in kv[1].split(',')))
            else:
                print(f"Unknown argument: {arg}")
                printHelp=True
                break
        else:
            files.extend(
                findFiles(arg,matchType=1,recursive=recursive))
    if not cmdline:
        print("No command line specified")
        printHelp=True
    else:
        multi=MultiExecute(
            cmdline,
            files,
            allowDuplicates,
            numThreads,
            fileEnvKey,
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
            showMaximized)
        results=multi.run()
        for url,result in results:
            print(f"{url}\n--------------------\n{result}")
    if printHelp:
        print("Usage: multiExecute.py [options] files -- command line to execute") # noqa: E501
        print("  wherin $FILE in the command line is placeholder for each file") # noqa: E501
        print("Options:")
        print("  -h, --help ........ Show this help message and exit")
        print("  --allowDuplicates . Allow same file to be processed multiple times") # noqa: E501
        print("  --numThreads ...... Number of threads to use")
        print("  --fileEnvKey ...... Environment variable key for the file path") # noqa: E501
        print("  --shell ........... Use the shell to execute the command")
        print("  --detach .......... Run the command in detached mode")
        print("  --debug ........... Enable debug mode")
        print("  --workingDirectory .. Set the working directory for the command") # noqa: E501
        print("  --environmentVariables .. Set environment variables for the command") # noqa: E501
        print("  --runCallbacks .... Enable running callbacks after execution")
        print("  --priority ........ Set the priority of the command")
        print("  --ansiHandling .... Handle ANSI escape codes in the output")
        print("  --showHidden ...... Show hidden windows")
        print("  --showMinimized ... Show minimized windows")
        print("  --showMaximized ... Show maximized windows")
        return -1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(cmdline(sys.argv[1:]))
