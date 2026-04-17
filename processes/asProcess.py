"""
Convert whatever into a process
"""
import typing
import psutil
if typing.TYPE_CHECKING:
    from .process import Process


class ClassWithPid(typing.Protocol):
    """
    Any class that contains a compatible pid member
    """
    pid:"ProcessCompatible"
class ClassWithProcess(typing.Protocol):
    """
    Any class that contains a compatible process member
    """
    process:"ProcessCompatible"


ProcessCompatible=typing.Union[
    int,"Process",ClassWithPid,ClassWithProcess,psutil.Process]


def asProcess(proc:ProcessCompatible)->"Process":
    """
    Always return a Process
    """
    from .process import Process
    if not isinstance(proc,Process):
        if isinstance(proc,int):
            proc=Process(proc)
        elif hasattr(proc,'pid'):
            proc=asProcess(int(proc.pid)) # type: ignore
        elif hasattr(proc,'process'):
            proc=asProcess(proc.process) # type: ignore
        else:
            raise ValueError(f'Unable to convert type "{type(proc)}"')
    return proc
