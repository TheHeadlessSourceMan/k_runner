"""
This module is for smartly running system commands
and processing their io streams.
"""
from .kRunnerTools import *
from .pyErrRun import *
from .runPythonFile import *
from .runSomething import *
from .cmdline import *

from .ui import *
import k_runner.ui # pylint: disable=wrong-import-order
uifiddle=k_runner.ui # legacy support
windowManipulator=k_runner.ui # legacy support

from .processes import * # noqa: E402 # pylint: disable=wrong-import-position
import k_runner.processes # noqa: E402,E501 # pylint: disable=wrong-import-order,wrong-import-position
processPlayset=k_runner.processes # legacy support
processManipulator=k_runner.processes # legacy support
possiblyRunningApplication=k_runner.processes # legacy support
