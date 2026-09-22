"""
This module is for smartly running system commands
and processing their io streams.
"""
import os
from .cmdline import *
from .environmentVariables import *
from .kRunnerTools import *
from .pyErrRun import *
from .runPythonFile import *
from .runSomething import *
from .osrun import *
from .osRunJob import *
from .osRunResult import *
from .dataRecievedCallbacks import *
from .filterRun import *
from .multiExecute import *
from .processWatcher import *

if os.name == "nt":
    from ._kRunnerToolsWindows import *
else:
    from ._kRunnerToolsLinux import *

from .ui import *
import k_runner.ui # pylint: disable=wrong-import-order # type: ignore
import k_runner.ui as uifiddle # legacy support # type: ignore
import k_runner.ui as windowManipulator # legacy support # type: ignore

from .processes import * # noqa: E402 # pylint: disable=wrong-import-position
import k_runner.processes # noqa: E402,E501 # pylint: disable=wrong-import-order,wrong-import-position # type: ignore
import k_runner.processes as processPlayset # legacy support # type: ignore
import k_runner.processes as processManipulator # legacy support # type: ignore
import k_runner.processes as possiblyRunningApplication # legacy support # type: ignore # noqa: E501
