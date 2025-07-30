"""
Convert anything to a ui window
"""
import typing
from pathlib import Path
if typing.TYPE_CHECKING:
    from k_runner.processes import ProcessCompatible
    from k_runner.ui import UiComponentCompatible
    from .commandLine import CommandLineArguments


class ClassWithCmdline(typing.Protocol):
    """
    Any class that contains a compatible cmdline member
    """
    cmdline:"CommandLineArgumentsCompatible"
class ClassWithCommandLine(typing.Protocol):
    """
    Any class that contains a compatible commandLine member
    """
    commandLine:"CommandLineArgumentsCompatible"
class ClassWithCmdLine(typing.Protocol):
    """
    Any class that contains a compatible cmdLine member
    """
    cmdLine:"CommandLineArgumentsCompatible"


CommandLineArgumentsCompatible=typing.Union[
    str,Path,typing.Iterable[typing.Union[str,Path]],
    "CommandLineArguments","ProcessCompatible","UiComponentCompatible",
    ClassWithCommandLine,ClassWithCommandLine,ClassWithCmdLine]
CommandLineCompatible=CommandLineArgumentsCompatible
CmdLineArgumentsCompatible=CommandLineArgumentsCompatible
CmdlineArgumentsCompatible=CommandLineArgumentsCompatible


def asCommandLineArguments(
    cmdline:CommandLineCompatible
    )->"CommandLineArguments":
    """
    Always return a CommandLine
    """
    from .commandLine import CommandLineArguments
    if not isinstance(cmdline,CommandLineArguments):
        if hasattr(cmdline,'cmdline'):
            return asCommandLine(cmdline.cmdline) # type: ignore
        if hasattr(cmdline,'cmdLine'):
            return asCommandLine(cmdline.cmdLine) # type: ignore
        if hasattr(cmdline,'commandLine'):
            return asCommandLine(cmdline.commandLine) # type: ignore
        cmdline=CommandLineArguments(cmdline)
    return cmdline
asCommandLine=asCommandLineArguments
asCmdLine=asCommandLineArguments
asCmdine=asCommandLineArguments
