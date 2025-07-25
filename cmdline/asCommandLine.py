"""
Convert anything to a ui window
"""
import typing
from pathlib import Path
if typing.TYPE_CHECKING:
    from k_runner.processes import ProcessCompatible
    from k_runner.ui import UiComponentCompatible
    from .commandLine import CommandLine


class ClassWithCmdline(typing.Protocol):
    """
    Any class that contains a compatible cmdline member
    """
    cmdline:"CommandLineCompatible"


CommandLineCompatible=typing.Union[
    str,Path,typing.Iterable[typing.Union[str,Path]],
    "CommandLine","ProcessCompatible","UiComponentCompatible"]


def asCommandLine(
    cmdline:CommandLineCompatible
    )->"CommandLine":
    """
    Always return a CommandLine
    """
    from .commandLine import CommandLine
    if not isinstance(cmdline,CommandLine):
        if hasattr(cmdline,'cmdline'):
            return asCommandLine(cmdline)
        cmdline=CommandLine(cmdline)
    return cmdline
