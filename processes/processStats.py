"""
Runtime stats about a process
"""
import typing
import datetime
import threading
import time
if typing.TYPE_CHECKING:
    from .process import Process


CPUStatsChangeFn=typing.Callable[[float],None]
GPUStatsChangeFn=typing.Callable[[float],None]
MemStatsChangeFn=typing.Callable[[int],None]


class ProcessStats:
    """
    Runtime stats about a process
    """
    def __init__(self,process:"Process"):
        self.process=process

    def watch(self,
        cpuChangeFn:typing.Optional[CPUStatsChangeFn]=None,
        gpuChangeFn:typing.Optional[GPUStatsChangeFn]=None,
        memChangeFn:typing.Optional[MemStatsChangeFn]=None,
        cpuChangeThreshold:float=0.02, # 2% cpu change
        gpuChangeThreshold:float=0.02, # 2% gpu change
        memChangeThreshold:float=255, # 255 bytes change
        pollingIntervalSeconds:float=0.25
        )->threading.Thread:
        """
        Watch a program for changes.

        NOTE: this thread exits if the program exits
        so if you want you could block using watch(myFn).join()

        EXAMPLE:
        # Log the app resource usage over time to a json file
        stats=myProcess.stats
        f=open('process.log.json','a')
        def watchCB(na):
            # whenever something changes add the current state to the log file
            f.writeln(stats.jsonStr)
            f.flush()
        thread=f.watch(watchCB,watchCB,watchCB)
        # wait for the application to end
        thread.join()
        # log the summary and execution time
        f.writeln(stats.jsonStr)
        f.close()
        """
        def watcherFn():
            lastCpu=-99999
            lastGpu=-99999
            lastMem=-99999
            while not self.process.isFinished:
                # keep track so the same function is not called
                # more than once per loop
                loggedCpu=False
                loggedGpu=False
                if cpuChangeFn is not None:
                    cpu=self.currentCPU
                    if abs(cpu-lastCpu)>=cpuChangeThreshold:
                        cpuChangeFn(cpu)
                        lastCpu=cpu
                        loggedCpu=True
                if gpuChangeFn is not None \
                    and not (gpuChangeFn==cpuChangeFn and loggedCpu):
                    gpu=self.currentGPU
                    if abs(gpu-lastGpu)>=gpuChangeThreshold:
                        gpuChangeFn(gpu)
                        lastGpu=gpu
                        loggedGpu=True
                if memChangeFn is not None \
                    and not (memChangeFn==cpuChangeFn and loggedCpu) \
                    and not (memChangeFn==gpuChangeFn and loggedGpu):
                    mem=self.currentMem
                    if abs(mem-lastMem)>=memChangeThreshold:
                        memChangeFn(mem)
                        lastMem=mem
                time.sleep(pollingIntervalSeconds)
        return threading.Thread(target=watcherFn)

    @property
    def jsonObj(self):
        """
        Convert these stats to a json-compatible object

        If the process is running, it returns the current values.
        Otherwise it returns the top values and executuion time information.
        """
        ret={}
        ret['command']=self.process.commandLine
        if not self.process.isRunning:
            ret['cpu']=self.process.topCPU
            ret['gpu']=self.process.topGPU
            ret['mem']=self.process.topMem
            ret['startTime']=str(self.process.startTime)
            ret['endTime']=str(self.process.endTime)
            ret['executionTime']=str(self.process.executionTime)
            ret['returnCode']=self.process.returnCode
        else:
            ret['cpu']=self.process.currentCPU
            ret['gpu']=self.process.currentGPU
            ret['mem']=self.process.currentMem
            ret['startTime']=str(self.process.startTime)
        return ret

    @property
    def jsonStr(self)->str:
        """
        Convert these stats to a json string
        """
        import json
        return json.dumps(self.jsonObj)

    @property
    def currentCPU(self)->float:
        """
        Current CPU usage.

        Returns 0 if the process has finished.
        """
        return 0.0

    @property
    def topCPU(self)->float:
        """
        Max CPU usage.
        """
        return 0.0

    @property
    def currentGPU(self)->float:
        """
        Current GPU usage.

        Returns 0 if the process has finished.
        """
        return 0.0

    @property
    def topGPU(self)->float:
        """
        Max GPU usage.
        """
        return 0.0

    @property
    def currentMem(self)->int:
        """
        Current memory usage.

        Returns 0 if the process has finished.
        """
        return 0

    @property
    def topMem(self)->int:
        """
        Max memory usage.
        """
        return 0

    @property
    def startTime(self)->datetime.datetime:
        """
        Time the process was started
        """
        return self.process.startTime
    @property
    def endTime(self)->typing.Optional[datetime.datetime]:
        """
        Time the process ended
        (None if the process is still running)
        """
        return self.process.endTime
    @property
    def runTime(self)->typing.Optional[datetime.timedelta]:
        """
        Time it took the process to execute
        (None if the process is still running)
        """
        end=self.endTime
        if end is None:
            return None
        return end-self.startTime
    executionTime=runTime
