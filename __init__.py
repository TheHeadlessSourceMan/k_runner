"""
This module is for smartly running system commands
and processing their io streams.
"""
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

from .cmdline import *

from .ui import *
import k_runner.ui # pylint: disable=wrong-import-order
import k_runner.ui as uifiddle # legacy support
import k_runner.ui as windowManipulator # legacy support

from .processes import * # noqa: E402 # pylint: disable=wrong-import-position
import k_runner.processes # noqa: E402,E501 # pylint: disable=wrong-import-order,wrong-import-position
import k_runner.processes as processPlayset # legacy support
import k_runner.processes as processManipulator # legacy support
import k_runner.processes as possiblyRunningApplication # legacy support
