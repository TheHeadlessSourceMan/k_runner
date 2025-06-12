"""
Convert anything to a ui window
"""
import typing
from pathlib import Path
if typing.TYPE_CHECKING:
    from k_runner.processes import ProcessCompatible
    from k_runner.ui import UiComponentCompatible
    from .commandLine import CmdLineWrapper


class ClassWithCmdline(typing.Protocol):
    """
    Any class that contains a compatible cmdline member
    """
    cmdline:"CommandLineCompatible"


CommandLineCompatible=typing.Union[
    str,Path,typing.Iterable[typing.Union[str,Path]],
    "CmdLineWrapper","ProcessCompatible","UiComponentCompatible"]


def asCommandLine(cmdline:CommandLineCompatible):
    """
    Always return a CommandLine
    """
    from .commandLine import CmdLineWrapper
    if not isinstance(cmdline,CmdLineWrapper):
        if hasattr(cmdline,'cmdline'):
            return asCommandLine(cmdline)
        cmdline=CmdLineWrapper(cmdline)
    return cmdline
