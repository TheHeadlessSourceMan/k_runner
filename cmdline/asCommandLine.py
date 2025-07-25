"""
Convert anything to a ui window
"""
import typing
from pathlib import Path
if typing.TYPE_CHECKING:
    from k_runner.processes import ProcessCompatible
    from k_runner.ui import UiComponentCompatible
    from .commandLine import CommandLineWrapper


class ClassWithCmdline(typing.Protocol):
    """
    Any class that contains a compatible cmdline member
    """
    cmdline:"CommandLineCompatible"


CommandLineCompatible=typing.Union[
    str,Path,typing.Iterable[typing.Union[str,Path]],
    "CommandLineWrapper","ProcessCompatible","UiComponentCompatible"]


def asCommandLine(
    cmdline:CommandLineCompatible
    )->"CommandLineWrapper":
    """
    Always return a CommandLine
    """
    from .commandLine import CommandLineWrapper
    if not isinstance(cmdline,CommandLineWrapper):
        if hasattr(cmdline,'cmdline'):
            return asCommandLine(cmdline)
        cmdline=CommandLineWrapper(cmdline)
    return cmdline
