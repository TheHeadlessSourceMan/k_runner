"""
A group of processes
"""
import typing
from .process import Process,ProcessCompatible,asProcess


class ProcessGroup:
    """
    A group of processes
    """
    def __init__(self,
        processes:typing.Union[None,
            ProcessCompatible,typing.List[ProcessCompatible]]=None):
        if processes is None:
            processes=[]
        elif not hasattr(processes,'__iter__'):
            processes=(processes,)
        self._procs:typing.Set[Process]=set([asProcess(p) for p in processes])

    def append(self,
        processes:typing.Union[None,
            ProcessCompatible,typing.List[ProcessCompatible]]=None
        )->None:
        """
        Add more processes to the list
        """
        if processes is None:
            processes=[]
        elif not hasattr(processes,'__iter__'):
            processes=(processes,)
        self._procs.union([asProcess(p) for p in processes])
    add=append
    extend=append

    def __iter__(self)->typing.Iterator[Process]:
        return iter(self._procs)

    def __repr__(self)->str:
        return '\n'.join([repr(p) for p in self._procs])
